"""Create order_processing_steps table.

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

STATUS_VALUES = ("PENDING", "COMPLETED", "FAILED")


def upgrade() -> None:
    conn = op.get_bind()
    process_after_default = (
        sa.text("now()") if conn.dialect.name == "postgresql" else sa.text("(datetime('now'))")
    )
    if conn.dialect.name == "postgresql":
        status_type = sa.Enum(*STATUS_VALUES, name="processing_step_status", create_type=True)
    else:
        status_type = sa.String(32)

    op.create_table(
        "order_processing_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.String(36), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("status", status_type, nullable=False, server_default="PENDING"),
        sa.Column("retry", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "process_after",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=process_after_default,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=process_after_default,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_order_processing_steps_order_id"),
        "order_processing_steps",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_order_processing_steps_idempotency_key"),
        "order_processing_steps",
        ["idempotency_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_order_processing_steps_idempotency_key"),
        table_name="order_processing_steps",
    )
    op.drop_index(
        op.f("ix_order_processing_steps_order_id"),
        table_name="order_processing_steps",
    )
    op.drop_table("order_processing_steps")
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        sa.Enum(*STATUS_VALUES, name="processing_step_status").drop(conn, checkfirst=True)
