"""Sender loop: select pending tasks, send to webhooks, mark completed or create retry with backoff."""

import logging
from datetime import datetime

from app.config import Settings
from app.models import NotificationProcessingStep, ProcessingStepStatus

from step_processor import apply_step_result, run_loop
from app.sender.selector import select_pending_tasks
from app.sender.sending import build_payload, send_to_webhooks

logger = logging.getLogger(__name__)


def _create_next_step(step: NotificationProcessingStep, process_after: datetime) -> NotificationProcessingStep:
    return NotificationProcessingStep(
        notification_id=step.notification_id,
        status=ProcessingStepStatus.PENDING,
        process_after=process_after,
        retry=step.retry + 1,
    )


def _run_cycle_sync(settings: Settings) -> None:
    """One cycle: select tasks, send each, apply result. All in one session."""
    from app.db import SessionLocal

    session = SessionLocal()
    try:
        tasks = select_pending_tasks(session, settings)
        for step, notification, webhooks in tasks:
            try:
                if not webhooks:
                    step.status = ProcessingStepStatus.COMPLETED
                    session.commit()
                    continue
                payload = build_payload(notification)
                success = send_to_webhooks(
                    payload,
                    webhooks,
                    client_ref=notification.client_ref,
                    timeout_seconds=settings.sending_timeout_in_seconds,
                )
                apply_step_result(
                    session=session,
                    step=step,
                    success=success,
                    max_retry=settings.sending_max_retry,
                    completed_status=ProcessingStepStatus.COMPLETED,
                    failed_status=ProcessingStepStatus.FAILED,
                    create_next_step=_create_next_step,
                )
                session.commit()
            except Exception as e:
                logger.exception("Sender step failed step_id=%s: %s", step.id, e)
                session.rollback()
    finally:
        session.close()


async def run_sender(settings: Settings) -> None:
    """Loop: run sync cycle (select, send, update/insert retry), then sleep. Runs until cancelled."""
    await run_loop(
        lambda: _run_cycle_sync(settings),
        poll_interval=1.0,
        log_name="Sender",
    )
