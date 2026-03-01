"""Consume Debezium CDC events for orders; on create, insert order_processing_steps row."""

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


def _get_order_data_from_create_envelope(value: dict) -> tuple[str, str] | None:
    """Extract order_id and idempotency_key from Debezium envelope for create (op 'c') only."""
    if value.get("op") != "c":
        return None
    after = value.get("after")
    if not isinstance(after, dict):
        return None
    order_id = after.get("order_id")
    idempotency_key = after.get("idempotency_key")
    if not order_id or idempotency_key is None:
        return None
    return (order_id, idempotency_key)


def _insert_order_processing_step(
    session: Session, order_id: str, idempotency_key: str
) -> None:
    """Insert one order_processing_steps row: PENDING, retry 0, process_after now."""
    step = OrderProcessingStep(
        order_id=order_id,
        idempotency_key=idempotency_key,
        status=ProcessingStepStatus.PENDING,
        retry=0,
        process_after=datetime.now(timezone.utc),
    )
    session.add(step)
    session.commit()


async def process_cdc_envelope(envelope: dict, settings: Settings) -> bool:
    """Process one Debezium CDC envelope: on create, insert order_processing_steps row.
    Returns True if a row was inserted."""
    data = _get_order_data_from_create_envelope(envelope)
    if not data:
        return False
    order_id, idempotency_key = data
    session = SessionLocal()
    try:
        _insert_order_processing_step(session, order_id, idempotency_key)
        logger.info("Inserted order_processing_step order_id=%s", order_id)
        return True
    finally:
        session.close()


async def _process_orders_cdc_messages(settings: Settings) -> AsyncIterator[None]:
    """Consume orders CDC topic; on create event, insert step. Yields to allow cancellation."""
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
    """Run the orders CDC Kafka consumer until cancelled."""
    logger.info("Orders CDC consumer starting topic=%s", settings.kafka_orders_topic)
    try:
        async for _ in _process_orders_cdc_messages(settings):
            pass
    except asyncio.CancelledError:
        logger.info("Orders CDC consumer cancelled")
    except Exception as e:
        logger.exception("Orders CDC consumer failed: %s", e)
    finally:
        logger.info("Orders CDC consumer stopped")
