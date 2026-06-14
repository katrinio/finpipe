import os

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from src.storage.config import DatabaseConfig

pytest_plugins = (
    "tests.fixtures.storage",
    "tests.fixtures.telegram",
)


@pytest.fixture(autouse=True)
def _test_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Uses dedicated PostgreSQL test database and clears it per test."""

    database_url = DatabaseConfig.get_test_database_url()
    if "postgresql" not in database_url:
        return

    monkeypatch.setenv("DATABASE_URL", database_url)

    url = make_url(database_url)
    assert url.database.endswith("_test")
    print("ENV TEST_DATABASE_URL =", os.getenv("TEST_DATABASE_URL"))
    print("database_url =", database_url)
    _ensure_database_exists(database_url)
    engine = create_engine(database_url, future=True)
    try:
        with engine.begin() as connection:
            inspector = inspect(connection)

            table_names = [table_name for table_name in inspector.get_table_names() if table_name != "alembic_version"]

            if table_names:
                quoted_names = ", ".join(f'"{table_name}"' for table_name in table_names)

                connection.execute(text(f"TRUNCATE TABLE {quoted_names} RESTART IDENTITY CASCADE"))
    finally:
        engine.dispose()


def _ensure_database_exists(database_url: str) -> None:
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("Tests require PostgreSQL. Set TEST_DATABASE_URL to a PostgreSQL URL.")

    engine = None
    try:
        engine = create_engine(database_url, future=True)
        with engine.connect():
            return
    except OperationalError:
        pass
    finally:
        try:
            if engine is not None:
                engine.dispose()
        except Exception:
            pass

    admin_url = url.set(database="postgres")
    admin_engine = create_engine(admin_url, future=True, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": url.database},
            ).scalar_one_or_none()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    except Exception as exc:
        raise RuntimeError(f"PostgreSQL test database is unavailable: {type(exc).__name__}: {exc}. TEST_DATABASE_URL={database_url!r}") from exc
    finally:
        admin_engine.dispose()
