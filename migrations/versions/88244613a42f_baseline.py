"""baseline

Revision ID: 88244613a42f
Revises:
Create Date: 2026-06-13 17:23:47.387127

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "88244613a42f"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "allowed_users",
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("telegram_id"),
    )
    op.create_index("ix_allowed_users_telegram_id", "allowed_users", ["telegram_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("user_name", sa.String(), nullable=False),
        sa.Column("command", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("details", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_telegram_id", "audit_log", ["telegram_id"])

    op.create_table(
        "bank_account",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_telegram_id", sa.Integer(), nullable=False),
        sa.Column("account_holder", sa.String(), nullable=False),
        sa.Column("account_holder_email", sa.String(), nullable=True),
        sa.Column("account_holder_address", sa.String(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("bank_name", sa.String(), nullable=False),
        sa.Column("account_number", sa.String(), nullable=False),
        sa.Column("iban", sa.String(), nullable=False),
        sa.Column("bic", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bank_account_owner_telegram_id", "bank_account", ["owner_telegram_id"], unique=True)

    op.create_table(
        "company_profile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_telegram_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("company_address", sa.String(), nullable=False),
        sa.Column("registration_number", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("payment_number", sa.String(), nullable=True),
        sa.Column("payment_code", sa.String(), nullable=True),
        sa.Column("payment_description", sa.String(), nullable=True),
        sa.Column("service_agreement_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_profile_owner_telegram_id", "company_profile", ["owner_telegram_id"], unique=True)

    op.create_table(
        "document_generation_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(), nullable=False, server_default=sa.text("'salary_invoice'")),
        sa.Column("document_number", sa.String(), nullable=True),
        sa.Column("telegram_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'success'")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_generation_history_document_number", "document_generation_history", ["document_number"])
    op.create_index("ix_document_generation_history_document_type", "document_generation_history", ["document_type"])
    op.create_index("ix_document_generation_history_telegram_id", "document_generation_history", ["telegram_id"])

    op.create_table(
        "known_users",
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("telegram_id"),
    )
    op.create_index("ix_known_users_telegram_id", "known_users", ["telegram_id"])

    op.create_table(
        "oauth_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("telegram_username", sa.String(), nullable=True),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_oauth_sessions_state", "oauth_sessions", ["state"], unique=True)
    op.create_index("ix_oauth_sessions_telegram_id", "oauth_sessions", ["telegram_id"])

    op.create_table(
        "processed_messages",
        sa.Column("message_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("message_id"),
    )

    op.create_table(
        "signatures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_telegram_id", sa.Integer(), nullable=False),
        sa.Column("signature_path", sa.String(), nullable=False),
        sa.Column("signature_hash", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signatures_owner_telegram_id", "signatures", ["owner_telegram_id"], unique=True)

    op.create_table(
        "telegram_updates",
        sa.Column("update_id", sa.Integer(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("update_id"),
    )

    op.create_table(
        "user_config",
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("invoice_amount_eur", sa.Integer(), nullable=True),
        sa.Column("received_amount_eur", sa.Float(), nullable=True),
        sa.Column("exchange_amount_eur", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("telegram_id"),
    )

    op.create_table(
        "user_state_storage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_telegram_id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=31), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_state_storage_owner_telegram_id", "user_state_storage", ["owner_telegram_id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_user_state_storage_owner_telegram_id", table_name="user_state_storage")
    op.drop_table("user_state_storage")

    op.drop_table("user_config")
    op.drop_table("telegram_updates")

    op.drop_index("ix_signatures_owner_telegram_id", table_name="signatures")
    op.drop_table("signatures")

    op.drop_table("processed_messages")

    op.drop_index("ix_oauth_sessions_telegram_id", table_name="oauth_sessions")
    op.drop_index("ix_oauth_sessions_state", table_name="oauth_sessions")
    op.drop_table("oauth_sessions")

    op.drop_index("ix_known_users_telegram_id", table_name="known_users")
    op.drop_table("known_users")

    op.drop_index("ix_document_generation_history_telegram_id", table_name="document_generation_history")
    op.drop_index("ix_document_generation_history_document_type", table_name="document_generation_history")
    op.drop_index("ix_document_generation_history_document_number", table_name="document_generation_history")
    op.drop_table("document_generation_history")

    op.drop_index("ix_company_profile_owner_telegram_id", table_name="company_profile")
    op.drop_table("company_profile")

    op.drop_index("ix_bank_account_owner_telegram_id", table_name="bank_account")
    op.drop_table("bank_account")

    op.drop_index("ix_audit_log_telegram_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_allowed_users_telegram_id", table_name="allowed_users")
    op.drop_table("allowed_users")
