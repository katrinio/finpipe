import pytest
from sqlalchemy import create_engine, inspect, text

from src.storage.config import DatabaseConfig

pytest_plugins = (
    "tests.fixtures.storage",
    "tests.fixtures.telegram",
)


@pytest.fixture(autouse=True)
def _test_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Uses the configured PostgreSQL database for tests and clears it per test."""

    database_url = DatabaseConfig.get_database_url()
    monkeypatch.setenv("DATABASE_URL", database_url)

    engine = create_engine(database_url, future=True)
    try:
        with engine.begin() as connection:
            inspector = inspect(connection)
            table_names = inspector.get_table_names()
            if table_names:
                quoted_names = ", ".join(f'"{table_name}"' for table_name in table_names)
                connection.execute(text(f"TRUNCATE TABLE {quoted_names} RESTART IDENTITY CASCADE"))
    except Exception as exc:  # pragma: no cover - surfaces environment misconfiguration
        raise RuntimeError("PostgreSQL test database is unavailable. Set DATABASE_URL to a reachable PostgreSQL database.") from exc
    finally:
        engine.dispose()
