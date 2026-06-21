"""add company_email to company_profile and cc to pending_bank_reply

Revision ID: f1a2b3c4d5e6
Revises: c1d4e8f2a903
Create Date: 2026-06-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "c1d4e8f2a903"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("company_profile", sa.Column("company_email", sa.String(), nullable=True))
    op.add_column("pending_bank_reply", sa.Column("cc", sa.String(), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("company_profile", "company_email")
    op.drop_column("pending_bank_reply", "cc")
