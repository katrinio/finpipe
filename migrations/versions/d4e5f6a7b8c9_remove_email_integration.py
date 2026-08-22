"""remove email integration

Revision ID: d4e5f6a7b8c9
Revises: a1b2c3d4e5f6
Create Date: 2026-08-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("pending_bank_reply")
    op.drop_table("processed_messages")
    op.drop_table("oauth_sessions")
    op.drop_table("gmail_account")

    op.drop_column("company_profile", "company_email")
    op.drop_column("bank_account", "account_holder_email")
    op.drop_column("bank_account", "bank_confirmation_email_recipient")
    op.drop_column("bank_account", "bank_confirmation_email_subject_contains")
    op.drop_column("bank_account", "bank_slug")


def downgrade() -> None:
    op.add_column("bank_account", sa.Column("bank_slug", sa.String(), nullable=True))
    op.add_column("bank_account", sa.Column("bank_confirmation_email_subject_contains", sa.String(), nullable=True))
    op.add_column("bank_account", sa.Column("bank_confirmation_email_recipient", sa.String(), nullable=True))
    op.add_column("bank_account", sa.Column("account_holder_email", sa.String(), nullable=True))
    op.add_column("company_profile", sa.Column("company_email", sa.String(), nullable=True))

    op.create_table(
        "gmail_account",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("gmail_email", sa.String(), nullable=True),
        sa.Column("gmail_refresh_token", sa.String(), nullable=True),
        sa.Column("gmail_connected_at", sa.DateTime(), nullable=True),
        sa.Column("gmail_last_error", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
    )
    op.create_index(op.f("ix_gmail_account_owner_telegram_id"), "gmail_account", ["owner_telegram_id"], unique=True)
    op.create_table(
        "oauth_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("telegram_username", sa.String(), nullable=True),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("code_verifier", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
    )
    op.create_index(op.f("ix_oauth_sessions_state"), "oauth_sessions", ["state"], unique=True)
    op.create_index(op.f("ix_oauth_sessions_telegram_id"), "oauth_sessions", ["telegram_id"], unique=False)
    op.create_table(
        "processed_messages",
        sa.Column("message_id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
    )
    op.create_table(
        "pending_bank_reply",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True),
        sa.Column("thread_id", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("sender", sa.String(), nullable=False),
        sa.Column("cc", sa.String(), nullable=False, server_default=""),
        sa.Column("message_id", sa.String(), nullable=False),
        sa.Column("invoice_pdf_path", sa.String(), nullable=False),
        sa.Column("bank_confirmation_path", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
    )
