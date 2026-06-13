"""Alembic migration helpers."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from src.storage.orm.database import build_sqlite_url
from src.utils.credentials import EnvVar


def run_alembic_upgrade_head(db_path: Path) -> None:
    """Применяет миграции Alembic к указанной SQLite базе."""

    config = Config(str(EnvVar.PROJECT_ROOT / "alembic.ini"))
    config.attributes["skip_logging_config"] = True
    config.set_main_option("sqlalchemy.url", build_sqlite_url(db_path))
    command.upgrade(config, "head")
