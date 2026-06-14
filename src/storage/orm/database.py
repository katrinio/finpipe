"""Настройка SQLAlchemy engine и session factory."""

import logging
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.storage.config import DatabaseConfig
from src.storage.exceptions import StorageConfigurationError
from src.storage.orm.base import BaseModel

LOGGER = logging.getLogger(__name__)


class Database:
    """Инкапсулирует engine и фабрику сессий для persistence-слоя."""

    def __init__(self, database_url: str, echo: bool = False) -> None:
        self._database_url = database_url
        self._engine = create_engine(database_url, echo=echo, future=True)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False, class_=Session)
        self._configure_sqlite()

    @property
    def database_url(self) -> str:
        """Returns the configured database URL."""

        return self._database_url

    @property
    def engine(self) -> Engine:
        """Возвращает SQLAlchemy engine."""

        return self._engine

    def bind_models(self) -> None:
        """Привязывает ORM-модели к engine без создания или изменения схемы."""

        BaseModel.database = self

    def session(self) -> Session:
        """Создаёт новую независимую сессию."""

        return self._session_factory()

    def _configure_sqlite(self) -> None:
        if not self._is_sqlite():
            return

        sqlite_path = self._sqlite_file_path()
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)

        @event.listens_for(self._engine, "connect")
        def _set_sqlite_pragmas(dbapi_connection: Any, _connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.close()

    def _is_sqlite(self) -> bool:
        return self._database_url.startswith("sqlite")

    def _sqlite_file_path(self) -> Path:
        prefix = "sqlite:///"
        if not self._database_url.startswith(prefix):
            msg = "Only sqlite file URLs are supported by this helper"
            raise StorageConfigurationError(msg)
        return Path(self._database_url.removeprefix(prefix))


def build_sqlite_url(db_path: Path) -> str:
    """Строит SQLAlchemy URL для SQLite-файла."""

    return DatabaseConfig.build_sqlite_url(db_path)
