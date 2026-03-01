"""Select pending order_processing_steps (FOR UPDATE SKIP LOCKED)."""

from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import OrderProcessingStep, ProcessingStepStatus


def select_pending_tasks(
    session: Session,
    settings: Settings,
    *,
    limit: int = 100,
) -> list[OrderProcessingStep]:
    """Select steps ready to process: PENDING, process_after <= now, retry < max. FOR UPDATE SKIP LOCKED."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(OrderProcessingStep)
        .where(
            and_(
                OrderProcessingStep.status == ProcessingStepStatus.PENDING,
                OrderProcessingStep.process_after <= now,
                OrderProcessingStep.retry < settings.execution_max_retry,
            )
        )
        .with_for_update(skip_locked=True)
        .limit(limit)
    )
    return list(session.scalars(stmt).all())
