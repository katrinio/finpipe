"""Database helpers for tests."""

import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from src.storage.config import DatabaseConfig
from src.storage.orm import *  # noqa: F403
from src.storage.orm.base import BaseModel
from src.storage.orm.database import Database


def build_test_database_url(*_args: object, **_kwargs: object) -> str:
    """Returns the active PostgreSQL test database URL."""

    if _args:
        first_arg = _args[0]
        if isinstance(first_arg, Path):
            return f"sqlite:///{first_arg}"

    try:
        database_url = DatabaseConfig.get_test_database_url()
        if make_url(database_url).get_backend_name() == "postgresql" and _can_connect(database_url):
            return database_url
    except RuntimeError:
        pass

    sqlite_path = Path(tempfile.gettempdir()) / "finpipe_test.db"
    return f"sqlite:///{sqlite_path}"


def _can_connect(database_url: str) -> bool:
    engine = create_engine(database_url, future=True)
    try:
        with engine.connect():
            return True
    except OperationalError:
        return False
    finally:
        engine.dispose()


def initialize_test_database(database: Database) -> None:
    """Binds ORM models and creates tables for a test database."""

    database.bind_models()
    BaseModel.metadata.create_all(database.engine)


def initialize_test_database_from_url(database_url: str) -> Database:
    """Creates and initializes a test database from an explicit URL."""

    database = Database(database_url)
    initialize_test_database(database)
    return database
