"""add bank confirmation email settings to bank account

Revision ID: 5f0b5ef6d2e1
Revises: 3f6b4a87baee
Create Date: 2026-06-17 13:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5f0b5ef6d2e1"
down_revision: str | Sequence[str] | None = "3f6b4a87baee"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bank_account", sa.Column("bank_confirmation_email_sender", sa.String(), nullable=True))
    op.add_column("bank_account", sa.Column("bank_confirmation_email_recipient", sa.String(), nullable=True))
    op.add_column("bank_account", sa.Column("bank_confirmation_email_subject_contains", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("bank_account", "bank_confirmation_email_subject_contains")
    op.drop_column("bank_account", "bank_confirmation_email_recipient")
    op.drop_column("bank_account", "bank_confirmation_email_sender")
