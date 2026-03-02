"""Consume Debezium CDC events for orders table from Kafka; persist notifications."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator

import httpx
from aiokafka import AIOKafkaConsumer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Notification, NotificationProcessingStep, ProcessingStepStatus

logger = logging.getLogger(__name__)


async def process_cdc_envelope(envelope: dict, settings: Settings) -> bool:
    """Process one Debezium CDC envelope (create/update only): status from payload; client_ref from payload or order service.
    Returns True if a row was inserted, False if skipped (not c/u, no order_id, no status, or duplicate)."""
    if envelope.get("op") not in ("c", "u"):
        return False
    order_id = _get_order_id_from_envelope(envelope)
    if not order_id:
        return False
    status = _get_status_from_envelope(envelope)
    if not status:
        return False
    client_ref = _get_client_ref_from_envelope(envelope)
    if client_ref is None:
        client_ref = await _fetch_client_ref(settings, order_id)
    if client_ref is None:
        return False
    from app.db import SessionLocal

    session = SessionLocal()
    try:
        return _upsert_notification(session, client_ref, order_id, status)
    finally:
        session.close()


def _get_order_id_from_envelope(value: dict) -> str | None:
    """Extract order_id from Debezium envelope (create/update only; from after)."""
    if value.get("op") not in ("c", "u"):
        return None
    after = value.get("after")
    return after.get("order_id") if isinstance(after, dict) else None


def _get_status_from_envelope(value: dict) -> str | None:
    """Extract order status from Debezium envelope (create/update only; from after)."""
    if value.get("op") not in ("c", "u"):
        return None
    after = value.get("after")
    if isinstance(after, dict) and after.get("status"):
        return str(after["status"])
    return None


def _get_client_ref_from_envelope(value: dict) -> str | None:
    """Extract client_ref from Debezium envelope (create/update only; from after)."""
    if value.get("op") not in ("c", "u"):
        return None
    after = value.get("after")
    if isinstance(after, dict) and "client_ref" in after:
        return str(after["client_ref"]) if after["client_ref"] is not None else None
    return None


async def _fetch_client_ref(settings: Settings, order_id: str) -> str | None:
    """GET order by id from order service. Returns client_ref only, or None."""
    base = settings.order_service_url.rstrip("/")
    url = f"{base}/api/v1/orders/{order_id}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            return data.get("client_ref")
    except Exception as e:
        logger.warning("Failed to fetch order %s from order service: %s", order_id, e)
        return None


def _upsert_notification(session: Session, client_ref: str, order_id: str, order_status: str) -> bool:
    """Insert notification row and a PENDING step. Returns True if inserted, False if duplicate."""
    row = Notification(
        client_ref=client_ref,
        order_id=order_id,
        order_status=order_status,
    )
    session.add(row)
    try:
        session.flush()
        step = NotificationProcessingStep(
            notification_id=row.id,
            status=ProcessingStepStatus.PENDING,
            retry=0,
        )
        session.add(step)
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False


async def _process_orders_cdc_messages(
    settings: Settings,
) -> AsyncIterator[None]:
    """Consume orders CDC topic and persist notifications. Yields to allow cancellation."""
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
    """Run the orders CDC Kafka consumer until cancelled. Logs and swallows errors."""
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
