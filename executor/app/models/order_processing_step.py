"""Order processing step: one row per order to process (CDC creates with PENDING)."""

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ProcessingStepStatus(str, PyEnum):
    """Step status."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class OrderProcessingStep(Base):
    """One processing step for an order (created from CDC on new order)."""

    __tablename__ = "order_processing_steps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[ProcessingStepStatus] = mapped_column(
        Enum(ProcessingStepStatus),
        nullable=False,
        default=ProcessingStepStatus.PENDING,
    )
    retry: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    process_after: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
