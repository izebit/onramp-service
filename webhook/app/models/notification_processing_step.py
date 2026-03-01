"""Processing step for a notification: status and retry count."""

from enum import Enum as PyEnum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ProcessingStepStatus(str, PyEnum):
    """Step status."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class NotificationProcessingStep(Base):
    """One processing step for a notification (status + retry)."""

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
    retry: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
