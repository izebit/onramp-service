"""Order model."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


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
    quote_id: Mapped[str] = mapped_column(String(36), nullable=False)
    from_currency: Mapped[str] = mapped_column(String(16), nullable=False)
    to_currency: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    fee: Mapped[float] = mapped_column(Float, nullable=False)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    expired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
