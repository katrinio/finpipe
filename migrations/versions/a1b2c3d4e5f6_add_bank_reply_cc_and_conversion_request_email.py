"""add bank_reply_cc and conversion_request_email to bank_account

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-07-06 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bank_account", sa.Column("bank_reply_cc", sa.String(), nullable=True))
    op.add_column("bank_account", sa.Column("conversion_request_email_to", sa.String(), nullable=True))
    op.add_column("bank_account", sa.Column("conversion_request_email_cc", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("bank_account", "conversion_request_email_cc")
    op.drop_column("bank_account", "conversion_request_email_to")
    op.drop_column("bank_account", "bank_reply_cc")
