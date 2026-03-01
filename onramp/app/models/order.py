"""Order model."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db import Base
from app.schemas import OrderStatus


def _uuid_default() -> str:
    return str(uuid4())


class Order(Base):
    """Stored order (created from a validated quote)."""

    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_uuid_default,
    )
    client_ref: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    quote: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
