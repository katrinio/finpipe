"""Alembic migration helpers."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from src.storage.config import DatabaseConfig
from src.utils.credentials import EnvVar


def run_alembic_upgrade_head(database_url: str | Path | None = None) -> None:
    """Применяет миграции Alembic к указанной базе данных."""

    resolved_database_url = DatabaseConfig.get_database_url(database_url)
    config = Config(str(EnvVar.PROJECT_ROOT / "alembic.ini"))
    config.attributes["skip_logging_config"] = True
    config.attributes["database_url"] = resolved_database_url
    config.set_main_option("sqlalchemy.url", resolved_database_url)
    command.upgrade(config, "head")
