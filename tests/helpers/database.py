"""Alembic-backed database helpers for tests."""

from src.storage.migrations import run_alembic_upgrade_head
from src.storage.orm.database import Database


def initialize_test_database(database: Database) -> None:
    """Applies Alembic migrations and binds ORM models for a test database."""

    run_alembic_upgrade_head(database.database_url)
    database.bind_models()
