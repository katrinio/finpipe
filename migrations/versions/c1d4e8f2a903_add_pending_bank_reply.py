"""add pending_bank_reply table

Revision ID: c1d4e8f2a903
Revises: 9b2c7e4a1d8f
Create Date: 2026-06-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c1d4e8f2a903"
down_revision: str | Sequence[str] | None = ("9b2c7e4a1d8f", "b7d2e9f1c4a3")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pending_bank_reply",
        sa.Column("telegram_id", sa.BIGINT(), nullable=False),
        sa.Column("thread_id", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("sender", sa.String(), nullable=False),
        sa.Column("message_id", sa.String(), nullable=False),
        sa.Column("invoice_pdf_path", sa.String(), nullable=False),
        sa.Column("bank_confirmation_path", sa.String(), nullable=False),
        sa.Column("conversion_order_path", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint("telegram_id"),
    )


def downgrade() -> None:
    op.drop_table("pending_bank_reply")
