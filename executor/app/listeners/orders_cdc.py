"""Consume order CDC events; on new order create, enqueue for execution (insert order_processing_steps row)."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import SessionLocal
from app.models import OrderProcessingStep, ProcessingStepStatus

logger = logging.getLogger(__name__)


def _get_order_id_from_create_envelope(value: dict) -> str | None:
    """Extract order_id from Debezium envelope for create (op 'c') only."""
    if value.get("op") != "c":
        return None
    after = value.get("after")
    if not isinstance(after, dict):
        return None
    order_id = after.get("order_id")
    return order_id if order_id else None


def _insert_order_processing_step(session: Session, order_id: str) -> None:
    """Insert one order_processing_steps row (enqueue order for execution)."""
    step = OrderProcessingStep(
        order_id=order_id,
        status=ProcessingStepStatus.PENDING,
        retry=0,
        process_after=datetime.now(timezone.utc),
    )
    session.add(step)
    session.commit()


async def process_cdc_envelope(envelope: dict, settings: Settings) -> bool:
    """Process one order CDC envelope: on create, enqueue order for execution.
    Returns True if a row was inserted."""
    order_id = _get_order_id_from_create_envelope(envelope)
    if not order_id:
        return False
    session = SessionLocal()
    try:
        _insert_order_processing_step(session, order_id)
        logger.info("Inserted order_processing_step order_id=%s", order_id)
        return True
    finally:
        session.close()


async def _process_orders_cdc_messages(settings: Settings) -> AsyncIterator[None]:
    """Consume orders CDC topic; on create event, enqueue order for execution. Yields to allow cancellation."""
    servers = [s.strip() for s in settings.kafka_bootstrap_servers.split(",")]
    consumer = AIOKafkaConsumer(
        settings.kafka_orders_topic,
        bootstrap_servers=servers,
        group_id=settings.kafka_consumer_group,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )
    await consumer.start()
    try:
        async for msg in consumer:
            if msg.value is None:
                continue
            envelope = msg.value.get("payload", msg.value)
            if isinstance(envelope, dict):
                await process_cdc_envelope(envelope, settings)
            await consumer.commit()
            yield
    finally:
        await consumer.stop()


async def run_orders_cdc_consumer(settings: Settings) -> None:
    """Run the order CDC consumer until cancelled (enqueues new orders for execution)."""
    logger.info("Order CDC consumer starting topic=%s", settings.kafka_orders_topic)
    try:
        async for _ in _process_orders_cdc_messages(settings):
            pass
    except asyncio.CancelledError:
        logger.info("Order CDC consumer cancelled")
    except Exception as e:
        logger.exception("Order CDC consumer failed: %s", e)
    finally:
        logger.info("Order CDC consumer stopped")
