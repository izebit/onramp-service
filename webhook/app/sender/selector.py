"""Select pending notification_processing_steps (FOR UPDATE SKIP LOCKED)."""

from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Notification, NotificationProcessingStep, ProcessingStepStatus, WebHook


def select_pending_tasks(
    session: Session,
    settings: Settings,
    *,
    limit: int = 100,
) -> list[tuple[NotificationProcessingStep, Notification, list[WebHook]]]:
    """Select steps ready to process: PENDING, process_after <= now, retry < max. FOR UPDATE SKIP LOCKED.
    Max attempt is enforced at insert time (processor does not insert when retry >= max - 1)."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(NotificationProcessingStep)
        .where(
            and_(
                NotificationProcessingStep.status == ProcessingStepStatus.PENDING,
                NotificationProcessingStep.process_after <= now,
                NotificationProcessingStep.retry < settings.sending_max_retry,
            )
        )
        .with_for_update(skip_locked=True)
        .limit(limit)
    )
    steps = list(session.scalars(stmt).all())
    result: list[tuple[NotificationProcessingStep, Notification, list[WebHook]]] = []
    for step in steps:
        notification = session.get(Notification, step.notification_id)
        if not notification:
            step.status = ProcessingStepStatus.FAILED
            session.commit()
            continue
        webhooks = list(
            session.scalars(
                select(WebHook).where(WebHook.client_ref == notification.client_ref)
            ).all()
        )
        result.append((step, notification, webhooks))
    return result
