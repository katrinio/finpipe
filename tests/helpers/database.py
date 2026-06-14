"""Alembic-backed database helpers for tests."""

from src.storage.migrations import run_alembic_upgrade_head
from src.storage.orm.database import Database


def build_test_database_url(*_args: object, **_kwargs: object) -> str:
    """Returns the active PostgreSQL test database URL."""

    from src.storage.config import DatabaseConfig

    return DatabaseConfig.get_database_url()


def initialize_test_database(database: Database) -> None:
    """Applies Alembic migrations and binds ORM models for a test database."""

    run_alembic_upgrade_head()
    database.bind_models()


def initialize_test_database_from_url(database_url: str) -> Database:
    """Creates and initializes a test database from an explicit URL."""

    database = Database(database_url)
    initialize_test_database(database)
    return database
