"""Storage configuration helpers."""

from pathlib import Path

from src.utils.credentials import EnvVar


class DatabaseConfig:
    """Resolves the database URL used by the application and migrations."""

    ENV_NAME = "DATABASE_URL"
    DEFAULT_URL = "sqlite:///storage/database.db"

    @classmethod
    def get_database_url(cls, database_url: str | Path | None = None) -> str:
        """Returns an explicit database URL, env value, or the default SQLite URL."""

        if isinstance(database_url, Path):
            return cls.build_sqlite_url(database_url)
        if database_url:
            return database_url
        return EnvVar.get_optional_env(cls.ENV_NAME, cls.DEFAULT_URL)

    @staticmethod
    def build_sqlite_url(db_path: Path) -> str:
        """Builds a SQLite URL for compatibility and tests."""

        return f"sqlite:///{db_path}"
