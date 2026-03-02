"""Consume order_tasks CDC from Kafka; on create/update, set Order.status from task status."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from aiokafka import AIOKafkaConsumer
from sqlalchemy import update

from app.config import Settings
from app.db import SessionLocal
from app.models import Order
from app.schemas import OrderStatus

logger = logging.getLogger(__name__)

# Map executor OrderTask status to onramp Order status
_TASK_STATUS_TO_ORDER_STATUS = {
    "PROCESSING": OrderStatus.PROCESSING,
    "COMPLETED": OrderStatus.COMPLETED,
    "ERROR": OrderStatus.FAILED,
}


def _order_id_and_status_from_envelope(value: dict) -> tuple[str | None, OrderStatus | None]:
    """Extract order_id and status from Debezium envelope (op 'c' or 'u'). Returns (order_id, order_status) or (None, None)."""
    op = value.get("op")
    if op not in ("c", "u"):
        return None, None
    after = value.get("after")
    if not isinstance(after, dict):
        return None, None
    order_id = after.get("order_id")
    task_status = after.get("status")
    if not order_id or not task_status:
        return None, None
    order_status = _TASK_STATUS_TO_ORDER_STATUS.get(task_status.upper() if isinstance(task_status, str) else None)
    if order_status is None:
        return None, None
    return order_id, order_status


def _apply_order_task_update(order_id: str, order_status: OrderStatus) -> bool:
    """Update Order.status by order_id. Returns True if a row was updated."""
    session = SessionLocal()
    try:
        result = session.execute(
            update(Order).where(Order.order_id == order_id).values(status=order_status)
        )
        session.commit()
        return result.rowcount > 0
    finally:
        session.close()


async def process_order_task_envelope(envelope: dict, settings: Settings) -> bool:
    """Process one order_tasks CDC envelope: update Order.status from task status.
    Returns True if an order was updated."""
    order_id, order_status = _order_id_and_status_from_envelope(envelope)
    if not order_id or not order_status:
        return False
    updated = _apply_order_task_update(order_id, order_status)
    if updated:
        logger.info("Updated order status order_id=%s status=%s", order_id, order_status.value)
    return updated


async def _process_order_tasks_cdc_messages(settings: Settings) -> AsyncIterator[None]:
    """Consume order_tasks CDC topic; on create/update, sync Order.status. Yields to allow cancellation."""
    servers = [s.strip() for s in settings.kafka_bootstrap_servers.split(",")]
    consumer = AIOKafkaConsumer(
        settings.kafka_order_tasks_topic,
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
                await process_order_task_envelope(envelope, settings)
            await consumer.commit()
            yield
    finally:
        await consumer.stop()


async def run_order_tasks_cdc_consumer(settings: Settings) -> None:
    """Run the order_tasks CDC consumer until cancelled (updates Order.status from task status)."""
    logger.info("Order tasks CDC consumer starting topic=%s", settings.kafka_order_tasks_topic)
    try:
        async for _ in _process_order_tasks_cdc_messages(settings):
            pass
    except asyncio.CancelledError:
        logger.info("Order tasks CDC consumer cancelled")
    except Exception as e:
        logger.exception("Order tasks CDC consumer failed: %s", e)
    finally:
        logger.info("Order tasks CDC consumer stopped")
