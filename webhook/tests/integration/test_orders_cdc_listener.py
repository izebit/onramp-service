"""Integration tests for orders CDC listener: process_cdc_envelope with real PostgreSQL."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select


def _debezium_envelope(order_id: str, op: str = "c") -> dict:
    """Minimal Debezium envelope for orders table."""
    if op in ("c", "u"):
        return {"op": op, "after": {"order_id": order_id, "client_ref": "ignored", "status": "PENDING"}}
    return {"op": op, "before": {"order_id": order_id}}


@pytest.mark.integration
def test_process_cdc_envelope_inserts_notification(
    settings,
    db_session,
    integration_engine,
) -> None:
    """Process a CDC envelope with mocked order service: notification and PENDING step created."""
    from app.models import Notification, NotificationProcessingStep, ProcessingStepStatus
    from app.listeners.orders_cdc import process_cdc_envelope

    order_id = "550e8400-e29b-41d4-a716-446655440000"
    envelope = _debezium_envelope(order_id)
    with patch(
        "app.listeners.orders_cdc._fetch_order_status",
        new_callable=AsyncMock,
        return_value=("client-123", "COMPLETED"),
    ):
        result = asyncio.run(process_cdc_envelope(envelope, settings))
    assert result is True
    rows = list(db_session.scalars(select(Notification)).all())
    assert len(rows) == 1
    assert rows[0].client_ref == "client-123"
    assert rows[0].order_id == order_id
    assert rows[0].order_status == "COMPLETED"
    steps = list(
        db_session.scalars(
            select(NotificationProcessingStep).where(
                NotificationProcessingStep.notification_id == rows[0].id
            )
        ).all()
    )
    assert len(steps) == 1
    assert steps[0].status == ProcessingStepStatus.PENDING


@pytest.mark.integration
def test_process_cdc_envelope_duplicate_ignored(
    settings,
    db_session,
    integration_engine,
) -> None:
    """Same (order_id, order_status) twice: second call does not insert, returns False."""
    from app.models import Notification
    from app.listeners.orders_cdc import process_cdc_envelope

    order_id = "660e8400-e29b-41d4-a716-446655440001"
    envelope = _debezium_envelope(order_id)
    with patch(
        "app.listeners.orders_cdc._fetch_order_status",
        new_callable=AsyncMock,
        return_value=("client-456", "PENDING"),
    ):
        first = asyncio.run(process_cdc_envelope(envelope, settings))
        second = asyncio.run(process_cdc_envelope(envelope, settings))
    assert first is True
    assert second is False
    rows = list(db_session.scalars(select(Notification).where(Notification.order_id == order_id)).all())
    assert len(rows) == 1
    assert rows[0].order_status == "PENDING"


@pytest.mark.integration
def test_process_cdc_envelope_no_order_id_skipped(settings) -> None:
    """Envelope without order_id: no insert, returns False."""
    from app.listeners.orders_cdc import process_cdc_envelope

    envelope = {"op": "c", "after": {"client_ref": "x"}}
    with patch(
        "app.listeners.orders_cdc._fetch_order_status",
        new_callable=AsyncMock,
        return_value=("client-1", "PENDING"),
    ):
        result = asyncio.run(process_cdc_envelope(envelope, settings))
    assert result is False


@pytest.mark.integration
def test_process_cdc_envelope_fetch_failure_skipped(settings, db_session) -> None:
    """Order service returns None (e.g. 404): no insert, returns False."""
    from app.models import Notification
    from app.listeners.orders_cdc import process_cdc_envelope

    order_id = "770e8400-e29b-41d4-a716-446655440002"
    envelope = _debezium_envelope(order_id)
    with patch(
        "app.listeners.orders_cdc._fetch_order_status",
        new_callable=AsyncMock,
        return_value=None,
    ):
        result = asyncio.run(process_cdc_envelope(envelope, settings))
    assert result is False
    rows = list(db_session.scalars(select(Notification).where(Notification.order_id == order_id)).all())
    assert len(rows) == 0
