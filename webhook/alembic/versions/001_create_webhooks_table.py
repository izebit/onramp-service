"""Create webhooks table.

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
    op.create_index(
        op.f("ix_webhooks_client_ref"),
        "webhooks",
        ["client_ref"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_webhooks_client_ref"), table_name="webhooks")
    op.drop_table("webhooks")
