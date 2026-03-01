"""Integration tests for invoker: select pending steps, execute payment, mark completed or create retry."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.models import OrderProcessingStep, ProcessingStepStatus
from app.invoker.processor import _run_cycle_sync
from app.invoker.selector import select_pending_tasks


def _create_order_processing_step(
    db_session,
    order_id: str | None = None,
    process_after: datetime | None = None,
    retry: int = 0,
) -> OrderProcessingStep:
    """Insert a PENDING order_processing_step. Returns the step."""
    import uuid
    if order_id is None:
        order_id = str(uuid.uuid4())
    if process_after is None:
        process_after = datetime.now(timezone.utc)
    step = OrderProcessingStep(
        order_id=order_id,
        status=ProcessingStepStatus.PENDING,
        process_after=process_after,
        retry=retry,
    )
    db_session.add(step)
    db_session.commit()
    db_session.refresh(step)
    return step


@pytest.mark.integration
def test_invoker_step_completed_when_payment_succeeds(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """Pending step: when execute_payment returns success, step is marked COMPLETED."""
    step = _create_order_processing_step(db_session, order_id="ord-success-001")

    with patch("app.invoker.processor.execute_payment", return_value="success"):
        _run_cycle_sync(settings)

    db_session.refresh(step)
    assert step.status == ProcessingStepStatus.COMPLETED


@pytest.mark.integration
def test_invoker_step_failed_creates_retry_when_payment_fails(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """When execute_payment returns error, step is FAILED and a new PENDING step is created with process_after set."""
    step = _create_order_processing_step(db_session, order_id="ord-retry-001")

    with patch("app.invoker.processor.execute_payment", return_value="error"):
        _run_cycle_sync(settings)

    db_session.refresh(step)
    assert step.status == ProcessingStepStatus.FAILED

    steps = list(
        db_session.scalars(
            select(OrderProcessingStep)
            .where(OrderProcessingStep.order_id == step.order_id)
            .order_by(OrderProcessingStep.id)
        ).all()
    )
    assert len(steps) == 2
    new_step = steps[1]
    assert new_step.status == ProcessingStepStatus.PENDING
    assert new_step.process_after is not None
    assert new_step.retry == 1


@pytest.mark.integration
def test_invoker_payment_succeeds_only_on_second_attempt(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """First payment fails, retry step is created; second cycle succeeds and marks step COMPLETED."""
    step = _create_order_processing_step(db_session, order_id="ord-second-001")

    with patch("app.invoker.processor.execute_payment", side_effect=["error", "success"]):
        _run_cycle_sync(settings)
        db_session.refresh(step)
        assert step.status == ProcessingStepStatus.FAILED

        steps = list(
            db_session.scalars(
                select(OrderProcessingStep)
                .where(OrderProcessingStep.order_id == step.order_id)
                .order_by(OrderProcessingStep.id)
            ).all()
        )
        assert len(steps) == 2
        retry_step = steps[1]
        retry_step.process_after = datetime.now(timezone.utc) - timedelta(seconds=1)
        db_session.commit()

        _run_cycle_sync(settings)

        db_session.refresh(retry_step)
        assert retry_step.status == ProcessingStepStatus.COMPLETED


@pytest.mark.integration
def test_invoker_tasks_not_run_when_process_after_in_future(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """When steps have process_after in the future, they are not selected and stay PENDING."""
    step = _create_order_processing_step(db_session, order_id="ord-delayed-001")
    step.process_after = datetime.now(timezone.utc) + timedelta(seconds=60)
    db_session.commit()
    db_session.refresh(step)

    with patch("app.invoker.processor.execute_payment") as mock_execute:
        _run_cycle_sync(settings)

    mock_execute.assert_not_called()
    db_session.refresh(step)
    assert step.status == ProcessingStepStatus.PENDING


@pytest.mark.integration
def test_invoker_select_pending_tasks_returns_ready_steps(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """select_pending_tasks returns only steps that are PENDING, process_after <= now, retry < max."""
    step = _create_order_processing_step(db_session, order_id="ord-select-001")
    step.process_after = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    db_session.refresh(step)

    tasks = select_pending_tasks(db_session, settings)
    assert len(tasks) == 1
    assert tasks[0].id == step.id
    assert tasks[0].order_id == "ord-select-001"
    assert tasks[0].retry == 0


@pytest.mark.integration
def test_invoker_execute_payment_called_with_order_id_and_settings(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """When running a cycle, execute_payment is called with step's order_id and settings."""
    order_id = "ord-call-args-123"
    step = _create_order_processing_step(db_session, order_id=order_id)

    with patch("app.invoker.processor.execute_payment", return_value="success") as mock_execute:
        _run_cycle_sync(settings)

    assert mock_execute.called
    calls_with_order_id = [c[0][0] for c in mock_execute.call_args_list]
    assert order_id in calls_with_order_id
    # Our call should have (order_id, settings)
    for call_args in mock_execute.call_args_list:
        if call_args[0][0] == order_id:
            assert call_args[0][1] is settings
            break
