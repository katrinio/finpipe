"""bank flow refactor: bank_slug, drop bank-specific email fields, drop conversion_order_path

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-07-06 00:00:00.000000

Changes:
- bank_account: add bank_slug, drop bank_confirmation_email_sender,
  bank_reply_cc, conversion_request_email_to, conversion_request_email_cc
- pending_bank_reply: drop conversion_order_path
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bank_account", sa.Column("bank_slug", sa.String(), nullable=True))
    op.drop_column("bank_account", "bank_confirmation_email_sender")

    op.drop_column("pending_bank_reply", "conversion_order_path")


def downgrade() -> None:
    op.add_column("pending_bank_reply", sa.Column("conversion_order_path", sa.String(), nullable=False, server_default=""))

    op.drop_column("bank_account", "bank_slug")
    op.add_column("bank_account", sa.Column("bank_confirmation_email_sender", sa.String(), nullable=True))
