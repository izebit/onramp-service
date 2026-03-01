"""Create order_tasks table.

Revision ID: 002
Revises: 001
Create Date: 2025-03-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ORDER_TASK_STATUS_VALUES = ("PROCESSING", "COMPLETED", "ERROR")


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        status_type = sa.Enum(
            *ORDER_TASK_STATUS_VALUES, name="order_task_status", create_type=True
        )
    else:
        status_type = sa.String(32)

    op.create_table(
        "order_tasks",
        sa.Column("order_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            status_type,
            nullable=False,
            server_default="PROCESSING",
        ),
        sa.PrimaryKeyConstraint("order_id"),
    )


def downgrade() -> None:
    op.drop_table("order_tasks")
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        sa.Enum(*ORDER_TASK_STATUS_VALUES, name="order_task_status").drop(
            conn, checkfirst=True
        )
