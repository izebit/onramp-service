"""Sender loop: select pending tasks, send to webhooks, mark completed or create retry with backoff."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import NotificationProcessingStep, ProcessingStepStatus

from app.sender.backoff import retry_delay_seconds
from app.sender.selector import select_pending_tasks
from app.sender.sending import build_payload, send_to_webhooks

logger = logging.getLogger(__name__)


def _apply_result(
    session: Session,
    step: NotificationProcessingStep,
    notification_id: int,
    success: bool,
    settings: Settings,
) -> None:
    """Mark step completed or failed; on failure create new PENDING step with delayed process_after if attempt count < max."""
    if success:
        step.status = ProcessingStepStatus.COMPLETED
        session.commit()
        return
    step.status = ProcessingStepStatus.FAILED
    session.flush()
    if step.attempt_count >= settings.sending_max_retry:
        session.commit()
        return
    delay = retry_delay_seconds(step.attempt_count - 1)
    process_after = datetime.now(timezone.utc) + timedelta(seconds=delay)
    new_step = NotificationProcessingStep(
        notification_id=notification_id,
        status=ProcessingStepStatus.PENDING,
        process_after=process_after,
        attempt_count=step.attempt_count + 1,
    )
    session.add(new_step)
    session.commit()


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
                success = send_to_webhooks(payload, webhooks, timeout_seconds=settings.sending_timeout_in_seconds)
                _apply_result(session, step, step.notification_id, success, settings)
            except Exception as e:
                logger.exception("Sender step failed step_id=%s: %s", step.id, e)
                session.rollback()
    finally:
        session.close()


async def run_sender(settings: Settings) -> None:
    """Loop: run sync cycle in executor (select, send, update/insert retry), then sleep. Runs until cancelled."""
    logger.info("Sender starting max_retry=%s", settings.sending_max_retry)
    loop = asyncio.get_running_loop()
    poll_interval = 1.0
    try:
        while True:
            try:
                await loop.run_in_executor(None, lambda: _run_cycle_sync(settings))
            except Exception as e:
                logger.exception("Sender cycle failed: %s", e)
            await asyncio.sleep(poll_interval)
    except asyncio.CancelledError:
        logger.info("Sender cancelled")
    finally:
        logger.info("Sender stopped")
