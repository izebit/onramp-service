"""Integration tests for order CDC listener: process_cdc_envelope with real PostgreSQL."""

import asyncio

import pytest
from sqlalchemy import select

from app.models import OrderProcessingStep, ProcessingStepStatus


def _create_envelope(order_id: str, op: str = "c") -> dict:
    """Minimal Debezium envelope for orders table (create)."""
    if op == "c":
        return {"op": op, "after": {"order_id": order_id}}
    return {"op": op, "before": {"order_id": order_id}, "after": {"order_id": order_id}}


@pytest.mark.integration
def test_process_cdc_envelope_inserts_order_processing_step(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """Process a create CDC envelope: one order_processing_steps row with PENDING, retry 0."""
    from app.listeners.orders_cdc import process_cdc_envelope

    order_id = "550e8400-e29b-41d4-a716-446655440000"
    envelope = _create_envelope(order_id)
    result = asyncio.run(process_cdc_envelope(envelope, settings))
    assert result is True
    steps = list(
        db_session.scalars(
            select(OrderProcessingStep).where(OrderProcessingStep.order_id == order_id)
        ).all()
    )
    assert len(steps) == 1
    step = steps[0]
    assert step.order_id == order_id
    assert step.status == ProcessingStepStatus.PENDING
    assert step.retry == 0
    assert step.process_after is not None
    assert step.created_at is not None


@pytest.mark.integration
def test_process_cdc_envelope_op_update_skipped(settings, db_session, _patch_app_db) -> None:
    """Envelope with op 'u' (update): no insert, returns False."""
    from app.listeners.orders_cdc import process_cdc_envelope

    order_id = "660e8400-e29b-41d4-a716-446655440001"
    envelope = _create_envelope(order_id, op="u")
    result = asyncio.run(process_cdc_envelope(envelope, settings))
    assert result is False
    steps = list(
        db_session.scalars(
            select(OrderProcessingStep).where(OrderProcessingStep.order_id == order_id)
        ).all()
    )
    assert len(steps) == 0


@pytest.mark.integration
def test_process_cdc_envelope_no_order_id_skipped(settings, db_session, _patch_app_db) -> None:
    """Envelope without order_id in after: no insert, returns False."""
    from app.listeners.orders_cdc import process_cdc_envelope

    envelope = {"op": "c", "after": {}}
    result = asyncio.run(process_cdc_envelope(envelope, settings))
    assert result is False


@pytest.mark.integration
def test_process_cdc_envelope_two_creates_insert_two_rows(
    settings, db_session, _patch_app_db
) -> None:
    """Two create envelopes (different order_id): two rows inserted."""
    from app.listeners.orders_cdc import process_cdc_envelope

    id1 = "a1b2c3d4-0000-4000-8000-000000000001"
    id2 = "a1b2c3d4-0000-4000-8000-000000000002"
    r1 = asyncio.run(process_cdc_envelope(_create_envelope(id1), settings))
    r2 = asyncio.run(process_cdc_envelope(_create_envelope(id2), settings))
    assert r1 is True
    assert r2 is True
    steps = list(
        db_session.scalars(
            select(OrderProcessingStep)
            .where(OrderProcessingStep.order_id.in_([id1, id2]))
            .order_by(OrderProcessingStep.order_id)
        ).all()
    )
    assert len(steps) == 2
    assert steps[0].order_id == id1
    assert steps[1].order_id == id2
