"""Create orders table.

Revision ID: 001
Revises:
Create Date: 2025-03-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.types import JSON

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUS_VALUES = ("PENDING", "COMPLETED", "FAILED")


def upgrade() -> None:
    """Create orders table with quote (JSON) and status."""
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        status_type = sa.Enum(*STATUS_VALUES, name="order_status", create_type=True)
    else:
        status_type = sa.String(16)

    op.create_table(
        "orders",
        sa.Column("order_id", sa.String(36), primary_key=True),
        sa.Column("client_ref", sa.String(255), nullable=False),
        sa.Column("quote", JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", status_type, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        op.f("ix_orders_client_ref"),
        "orders",
        ["client_ref"],
        unique=False,
    )


def downgrade() -> None:
    """Drop orders table."""
    op.drop_index(op.f("ix_orders_client_ref"), table_name="orders")
    op.drop_table("orders")
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        sa.Enum(*STATUS_VALUES, name="order_status").drop(conn, checkfirst=True)

