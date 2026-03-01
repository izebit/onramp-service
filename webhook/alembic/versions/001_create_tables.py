"""Create webhooks, notifications, and notification_processing_steps tables.

Revision ID: 001
Revises:
Create Date: 2025-03-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "webhooks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("client_ref", sa.String(255), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("signature_secret", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("client_ref", "url", name="uq_webhooks_client_ref_url"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_ref", sa.String(255), nullable=False),
        sa.Column("order_id", sa.String(36), nullable=False),
        sa.Column("order_status", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "order_id", "order_status", name="uq_notifications_order_id_order_status"
        ),
    )

    op.create_table(
        "notification_processing_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("notification_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("retry", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["notification_id"], ["notifications.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_notification_processing_steps_notification_id"),
        "notification_processing_steps",
        ["notification_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_notification_processing_steps_notification_id"),
        table_name="notification_processing_steps",
    )
    op.drop_table("notification_processing_steps")
    op.drop_table("notifications")
    op.drop_table("webhooks")
