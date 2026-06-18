"""Alembic migration helpers."""

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from src.storage.config import DatabaseConfig
from src.storage.orm import *  # noqa: F403
from src.storage.orm.base import BaseModel
from src.storage.orm.database import Database
from src.utils.credentials import EnvVar


def run_alembic_upgrade_head() -> None:
    """Применяет миграции Alembic к указанной базе данных."""

    database_url = DatabaseConfig.get_database_url()
    if make_url(database_url).get_backend_name() == "sqlite":
        database = Database(database_url)
        database.bind_models()
        BaseModel.metadata.create_all(database.engine)
        return

    config = Config(str(EnvVar.PROJECT_ROOT / "alembic.ini"))
    config.attributes["skip_logging_config"] = True
    config.attributes["database_url"] = database_url
    config.set_main_option("sqlalchemy.url", config.attributes["database_url"])
    command.upgrade(config, "head")
