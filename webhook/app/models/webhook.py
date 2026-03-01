"""WebHook model."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _uuid_default() -> str:
    return str(uuid4())


class WebHook(Base):
    """Stored webhook: client_ref + url."""

    __tablename__ = "webhooks"
    __table_args__ = (UniqueConstraint("client_ref", "url", name="uq_webhooks_client_ref_url"),)

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_uuid_default,
    )
    client_ref: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    signature_secret: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
