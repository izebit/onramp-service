"""Apply step result: mark completed/failed, optionally create retry step with backoff."""

from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from backoff import retry_delay_seconds


def apply_step_result(
    session: Session,
    step: Any,
    success: bool,
    max_retry: int,
    completed_status: Any,
    failed_status: Any,
    create_next_step: Callable[[Any, datetime], Any],
) -> None:
    """Mark step completed or failed; on failure create next step with backoff if retry < max."""
    if success:
        step.status = completed_status
        session.commit()
        return
    step.status = failed_status
    session.flush()
    if step.retry >= max_retry - 1:
        session.commit()
        return
    delay = retry_delay_seconds(step.retry)
    process_after = datetime.now(timezone.utc) + timedelta(seconds=delay)
    new_step = create_next_step(step, process_after)
    session.add(new_step)
    session.commit()
