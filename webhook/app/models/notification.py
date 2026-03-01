"""Notification model: one row per (order_id, order_status) for a client."""

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Notification(Base):
    """Stored notification: client_ref, order_id, order_status. Unique on (order_id, order_status)."""

    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("order_id", "order_status", name="uq_notifications_order_id_order_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_ref: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    order_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    order_status: Mapped[str] = mapped_column(String(32), nullable=False)
