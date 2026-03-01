"""Order task: one row per order, status PROCESSING | COMPLETED | ERROR. Created on CDC create."""

from enum import Enum as PyEnum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class OrderTaskStatus(str, PyEnum):
    """Order task status."""

    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class OrderTask(Base):
    """One task per order; created when order is enqueued, updated when step completes or fails for good."""

    __tablename__ = "order_tasks"

    order_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[OrderTaskStatus] = mapped_column(
        Enum(OrderTaskStatus),
        nullable=False,
        default=OrderTaskStatus.PROCESSING,
    )
