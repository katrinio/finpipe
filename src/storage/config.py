"""Storage configuration helpers."""

from src.utils.credentials import EnvVar


class DatabaseConfig:
    """Resolves the database URL used by the application and migrations."""

    ENV_NAME = "DATABASE_URL"
    DEFAULT_URL = "postgresql+psycopg://user:password@localhost:5432/finpipe"

    @classmethod
    def get_database_url(cls) -> str:
        """Returns the configured database URL."""

        return EnvVar.get_optional_env(cls.ENV_NAME, cls.DEFAULT_URL)
