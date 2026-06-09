"""Настройка SQLAlchemy engine, session factory и инициализации схемы."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

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
    def engine(self) -> Engine:
        """Возвращает SQLAlchemy engine."""

        return self._engine

    def initialize_schema(self) -> None:
        """Создаёт все известные ORM-таблицы.

        TODO: при появлении Alembic заменить `create_all` на управляемые миграции.
        """

        database_exists = self._sqlite_file_path().exists() if self._is_sqlite() else True
        BaseModel.metadata.create_all(self._engine)
        BaseModel.database = self
        if self._is_sqlite():
            self._sync_sqlite_schema()
        if not database_exists:
            LOGGER.info("Initialized SQLAlchemy storage at %s", self._database_url)

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
            raise ValueError(msg)
        return Path(self._database_url.removeprefix(prefix))

    def _sync_sqlite_schema(self) -> None:
        """Добавляет новые nullable-колонки в старую SQLite-схему."""

        with self._engine.begin() as connection:
            columns = {row[1] for row in connection.execute(text("PRAGMA table_info(user_config)")).all()}
            required_columns = {
                "signature_path": "TEXT NOT NULL DEFAULT ''",
                "signature_hash": "TEXT NOT NULL DEFAULT ''",
                "gmail_email": "TEXT",
                "gmail_refresh_token": "TEXT",
                "gmail_connected_at": "DATETIME",
                "gmail_last_error": "TEXT",
            }
            for column_name, column_sql in required_columns.items():
                if column_name not in columns:
                    connection.execute(text(f"ALTER TABLE user_config ADD COLUMN {column_name} {column_sql}"))


def build_sqlite_url(db_path: Path) -> str:
    """Строит SQLAlchemy URL для SQLite-файла."""

    return f"sqlite:///{db_path}"
