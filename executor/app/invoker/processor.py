"""Invoker loop: select pending steps, call payment provider, mark completed or create retry with backoff."""

import logging
from datetime import datetime

from app.config import Settings
from app.models import OrderProcessingStep, ProcessingStepStatus

from step_processor import apply_step_result, run_loop
from app.invoker.payment_provider import execute_payment
from app.invoker.selector import select_pending_tasks

logger = logging.getLogger(__name__)


def _create_next_step(step: OrderProcessingStep, process_after: datetime) -> OrderProcessingStep:
    return OrderProcessingStep(
        order_id=step.order_id,
        status=ProcessingStepStatus.PENDING,
        retry=step.retry + 1,
        process_after=process_after,
    )


def _run_cycle_sync(settings: Settings) -> None:
    """One cycle: select tasks, execute payment for each, apply result."""
    from app.db import SessionLocal

    session = SessionLocal()
    try:
        tasks = select_pending_tasks(session, settings)
        for step in tasks:
            try:
                result = execute_payment(step, settings)
                success = result == "success"
                apply_step_result(
                    session=session,
                    step=step,
                    success=success,
                    max_retry=settings.execution_max_retry,
                    completed_status=ProcessingStepStatus.COMPLETED,
                    failed_status=ProcessingStepStatus.FAILED,
                    create_next_step=_create_next_step,
                )
            except Exception as e:
                logger.exception("Invoker step failed step_id=%s: %s", step.id, e)
                session.rollback()
    finally:
        session.close()


async def run_invoker(settings: Settings) -> None:
    """Loop: run sync cycle (select, payment, update/insert retry), then sleep. Runs until cancelled."""
    await run_loop(
        lambda: _run_cycle_sync(settings),
        poll_interval=1.0,
        log_name="Invoker",
    )
