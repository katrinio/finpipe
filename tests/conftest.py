import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from src.storage.config import DatabaseConfig
from src.storage.orm import *  # noqa: F403
from src.storage.orm.base import BaseModel
from src.storage.orm.database import Database

pytest_plugins = (
    "tests.fixtures.storage",
    "tests.fixtures.telegram",
)
load_dotenv()


@pytest.fixture(autouse=True)
def _test_database_url(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Configures the test database per test type."""

    if _is_integration_test(request):
        database_url = _resolve_integration_database_url()
        if database_url is None:
            pytest.skip("PostgreSQL test database is unavailable")
        _ensure_database_initialized(database_url)
    else:
        database_url = _resolve_test_database_url(tmp_path_factory)
        if make_url(database_url).get_backend_name() == "sqlite":
            BaseModel.metadata.create_all(create_engine(database_url, future=True))
        _ensure_database_initialized(database_url)

    monkeypatch.setenv("DATABASE_URL", database_url)

    Database(database_url).bind_models()

    engine = create_engine(database_url, future=True)
    try:
        with engine.begin() as connection:
            inspector = inspect(connection)
            table_names = [t for t in inspector.get_table_names() if t != "alembic_version"]
            if table_names:
                if make_url(database_url).get_backend_name() == "sqlite":
                    for table_name in table_names:
                        connection.execute(text(f'DELETE FROM "{table_name}"'))
                else:
                    quoted = ", ".join(f'"{t}"' for t in table_names)
                    connection.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))
    finally:
        engine.dispose()


def _resolve_test_database_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    try:
        database_url = DatabaseConfig.get_test_database_url()
        if _can_connect(database_url):
            return database_url
    except RuntimeError:
        pass

    sqlite_path = tmp_path_factory.mktemp("db") / "test.db"
    return f"sqlite:///{sqlite_path}"


def _resolve_integration_database_url() -> str | None:
    try:
        database_url = DatabaseConfig.get_test_database_url()
    except RuntimeError:
        try:
            database_url = DatabaseConfig.get_database_url()
        except RuntimeError:
            return None
    if make_url(database_url).get_backend_name() != "postgresql":
        return None
    if not _can_connect(database_url):
        return None
    return database_url


def _is_integration_test(request: pytest.FixtureRequest) -> bool:
    return "tests/integration/" in str(request.node.path)


def _can_connect(database_url: str) -> bool:
    engine = create_engine(database_url, future=True)
    try:
        with engine.connect():
            return True
    except OperationalError:
        return False
    finally:
        engine.dispose()


def _can_connect(database_url: str) -> bool:
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        return True

    engine = None
    try:
        engine = create_engine(database_url, future=True)
        with engine.connect():
            return True
    except OperationalError:
        return False
    finally:
        if engine is not None:
            engine.dispose()


def _ensure_database_initialized(database_url: str) -> None:
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        return

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
