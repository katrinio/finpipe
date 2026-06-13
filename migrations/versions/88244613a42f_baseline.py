"""baseline

Revision ID: 88244613a42f
Revises:
Create Date: 2026-06-13 17:23:47.387127

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "88244613a42f"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE TABLE allowed_users (
            telegram_id INTEGER NOT NULL,
            username VARCHAR,
            role VARCHAR,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (telegram_id)
        )
        """
    )
    op.execute("CREATE INDEX ix_allowed_users_telegram_id ON allowed_users (telegram_id)")
    op.execute(
        """
        CREATE TABLE audit_log (
            id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            telegram_id INTEGER NOT NULL,
            user_name VARCHAR NOT NULL,
            command VARCHAR NOT NULL,
            status VARCHAR(20) NOT NULL,
            details VARCHAR,
            PRIMARY KEY (id)
        )
        """
    )
    op.execute("CREATE INDEX ix_audit_log_telegram_id ON audit_log (telegram_id)")
    op.execute(
        """
        CREATE TABLE bank_account (
            id INTEGER NOT NULL,
            owner_telegram_id INTEGER NOT NULL,
            account_holder VARCHAR NOT NULL,
            account_holder_email VARCHAR,
            account_holder_address VARCHAR,
            amount FLOAT,
            bank_name VARCHAR NOT NULL,
            account_number VARCHAR NOT NULL,
            iban VARCHAR NOT NULL,
            bic VARCHAR NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (id)
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX ix_bank_account_owner_telegram_id ON bank_account (owner_telegram_id)")
    op.execute(
        """
        CREATE TABLE company_profile (
            id INTEGER NOT NULL,
            owner_telegram_id INTEGER NOT NULL,
            company_name VARCHAR NOT NULL,
            company_address VARCHAR NOT NULL,
            registration_number VARCHAR,
            city VARCHAR,
            payment_number VARCHAR,
            payment_code VARCHAR,
            payment_description VARCHAR,
            service_agreement_date DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (id)
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX ix_company_profile_owner_telegram_id ON company_profile (owner_telegram_id)")
    op.execute(
        """
        CREATE TABLE document_generation_history (
            id INTEGER NOT NULL,
            document_type VARCHAR DEFAULT 'salary_invoice' NOT NULL,
            document_number VARCHAR,
            telegram_id INTEGER,
            status VARCHAR DEFAULT 'success' NOT NULL,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (id)
        )
        """
    )
    op.execute("CREATE INDEX ix_document_generation_history_document_number ON document_generation_history (document_number)")
    op.execute("CREATE INDEX ix_document_generation_history_document_type ON document_generation_history (document_type)")
    op.execute("CREATE INDEX ix_document_generation_history_telegram_id ON document_generation_history (telegram_id)")
    op.execute(
        """
        CREATE TABLE known_users (
            telegram_id INTEGER NOT NULL,
            username VARCHAR,
            first_name VARCHAR,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (telegram_id)
        )
        """
    )
    op.execute("CREATE INDEX ix_known_users_telegram_id ON known_users (telegram_id)")
    op.execute(
        """
        CREATE TABLE oauth_sessions (
            id INTEGER NOT NULL,
            state VARCHAR NOT NULL,
            telegram_id INTEGER NOT NULL,
            telegram_username VARCHAR,
            purpose VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            error_message VARCHAR,
            created_at DATETIME NOT NULL,
            expires_at DATETIME NOT NULL,
            used_at DATETIME,
            PRIMARY KEY (id)
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX ix_oauth_sessions_state ON oauth_sessions (state)")
    op.execute("CREATE INDEX ix_oauth_sessions_telegram_id ON oauth_sessions (telegram_id)")
    op.execute(
        """
        CREATE TABLE processed_messages (
            message_id VARCHAR NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (message_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE signatures (
            id INTEGER NOT NULL,
            owner_telegram_id INTEGER NOT NULL,
            signature_path VARCHAR NOT NULL,
            signature_hash VARCHAR NOT NULL,
            active BOOLEAN DEFAULT 1 NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (id)
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX ix_signatures_owner_telegram_id ON signatures (owner_telegram_id)")
    op.execute(
        """
        CREATE TABLE telegram_updates (
            update_id INTEGER NOT NULL,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (update_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE user_config (
            telegram_id INTEGER NOT NULL,
            invoice_amount_eur INTEGER,
            received_amount_eur FLOAT,
            exchange_amount_eur FLOAT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (telegram_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE user_state_storage (
            id INTEGER NOT NULL,
            owner_telegram_id INTEGER NOT NULL,
            state VARCHAR(31) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX ix_user_state_storage_owner_telegram_id ON user_state_storage (owner_telegram_id)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_user_state_storage_owner_telegram_id")
    op.execute("DROP TABLE IF EXISTS user_state_storage")
    op.execute("DROP TABLE IF EXISTS user_config")
    op.execute("DROP TABLE IF EXISTS telegram_updates")
    op.execute("DROP INDEX IF EXISTS ix_signatures_owner_telegram_id")
    op.execute("DROP TABLE IF EXISTS signatures")
    op.execute("DROP TABLE IF EXISTS processed_messages")
    op.execute("DROP INDEX IF EXISTS ix_oauth_sessions_telegram_id")
    op.execute("DROP INDEX IF EXISTS ix_oauth_sessions_state")
    op.execute("DROP TABLE IF EXISTS oauth_sessions")
    op.execute("DROP INDEX IF EXISTS ix_known_users_telegram_id")
    op.execute("DROP TABLE IF EXISTS known_users")
    op.execute("DROP INDEX IF EXISTS ix_document_generation_history_telegram_id")
    op.execute("DROP INDEX IF EXISTS ix_document_generation_history_document_type")
    op.execute("DROP INDEX IF EXISTS ix_document_generation_history_document_number")
    op.execute("DROP TABLE IF EXISTS document_generation_history")
    op.execute("DROP INDEX IF EXISTS ix_company_profile_owner_telegram_id")
    op.execute("DROP TABLE IF EXISTS company_profile")
    op.execute("DROP INDEX IF EXISTS ix_bank_account_owner_telegram_id")
    op.execute("DROP TABLE IF EXISTS bank_account")
    op.execute("DROP INDEX IF EXISTS ix_audit_log_telegram_id")
    op.execute("DROP TABLE IF EXISTS audit_log")
    op.execute("DROP INDEX IF EXISTS ix_allowed_users_telegram_id")
    op.execute("DROP TABLE IF EXISTS allowed_users")
