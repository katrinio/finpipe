"""simplify single owner architecture

Revision ID: e8f1a2b3c4d5
Revises: d4e5f6a7b8c9
Create Date: 2026-08-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e8f1a2b3c4d5"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("allowed_users")
    op.drop_table("known_users")
    op.drop_table("audit_log")
    op.drop_table("document_generation_history")
    op.drop_table("app_events")

    op.drop_column("bank_account", "amount")
    op.drop_column("user_config", "received_amount_eur")
    op.drop_column("user_config", "conversion_amount_eur")
    op.drop_column("user_config", "exchange_amount_eur")


def downgrade() -> None:
    op.add_column("user_config", sa.Column("exchange_amount_eur", sa.Float(), nullable=True))
    op.add_column("user_config", sa.Column("conversion_amount_eur", sa.Float(), nullable=True))
    op.add_column("user_config", sa.Column("received_amount_eur", sa.Float(), nullable=True))
    op.add_column("bank_account", sa.Column("amount", sa.Float(), nullable=True))

    op.create_table(
        "app_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
    )
    op.create_index(op.f("ix_app_events_created_at"), "app_events", ["created_at"])
    op.create_index(op.f("ix_app_events_event_type"), "app_events", ["event_type"])
    op.create_index(op.f("ix_app_events_severity"), "app_events", ["severity"])

    op.create_table(
        "document_generation_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_type", sa.String(), nullable=False, server_default="salary_invoice"),
        sa.Column("document_number", sa.String(), nullable=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="success"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
    )
    op.create_index("ix_document_generation_history_document_number", "document_generation_history", ["document_number"])
    op.create_index("ix_document_generation_history_document_type", "document_generation_history", ["document_type"])
    op.create_index("ix_document_generation_history_telegram_id", "document_generation_history", ["telegram_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("user_name", sa.String(), nullable=False),
        sa.Column("command", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("details", sa.String(), nullable=True),
    )
    op.create_index("ix_audit_log_telegram_id", "audit_log", ["telegram_id"])

    op.create_table(
        "known_users",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
    )
    op.create_index("ix_known_users_telegram_id", "known_users", ["telegram_id"])

    op.create_table(
        "allowed_users",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
    )
    op.create_index("ix_allowed_users_telegram_id", "allowed_users", ["telegram_id"])
