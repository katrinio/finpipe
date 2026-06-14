"""Storage configuration helpers."""

import os

from src.utils.credentials import EnvVar


class DatabaseConfig:
    """Resolves the database URL used by the application and migrations."""

    ENV_NAME = "DATABASE_URL"

    @classmethod
    def get_database_url(cls) -> str:
        """Returns the configured database URL."""

        return EnvVar.get_required_env(cls.ENV_NAME)

    @classmethod
    def get_test_database_url(cls) -> str:
        value = os.getenv("TEST_DATABASE_URL")

        if not value:
            raise RuntimeError("TEST_DATABASE_URL is not configured")

        return value
