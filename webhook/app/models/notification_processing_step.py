"""Processing step for a notification: status and process_after for backoff."""

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ProcessingStepStatus(str, PyEnum):
    """Step status."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class NotificationProcessingStep(Base):
    """One processing step for a notification (status + process_after)."""

    __tablename__ = "notification_processing_steps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    notification_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ProcessingStepStatus] = mapped_column(
        Enum(ProcessingStepStatus),
        nullable=False,
        default=ProcessingStepStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    process_after: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    retry: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
