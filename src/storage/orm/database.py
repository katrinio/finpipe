"""Настройка SQLAlchemy engine, session factory и инициализации схемы."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, Table, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateColumn

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
        """Приводит SQLite-схему к текущим ORM-моделям."""

        with self._engine.begin() as connection:
            for table in BaseModel.metadata.sorted_tables:
                self._sync_sqlite_table(connection, table)

    def _sync_sqlite_table(self, connection: Any, table: Table) -> None:
        existing_columns = self._get_sqlite_table_columns(connection, table.name)
        if not existing_columns:
            return

        model_columns = [column.name for column in table.columns]
        missing_columns = [column for column in table.columns if column.name not in existing_columns]
        extra_columns = [column_name for column_name in existing_columns if column_name not in model_columns]

        for column in missing_columns:
            connection.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {self._render_sqlite_column(column)}"))

        if extra_columns:
            self._rebuild_sqlite_table(connection, table)

    def _rebuild_sqlite_table(self, connection: Any, table: Table) -> None:
        temp_table_name = f"{table.name}__legacy"
        connection.execute(text(f'ALTER TABLE "{table.name}" RENAME TO "{temp_table_name}"'))
        table.create(connection)

        legacy_columns = self._get_sqlite_table_columns(connection, temp_table_name)
        model_columns = [column.name for column in table.columns]
        common_columns = [column_name for column_name in model_columns if column_name in legacy_columns]
        if common_columns:
            columns_sql = ", ".join(f'"{column_name}"' for column_name in common_columns)
            connection.execute(text(f'INSERT INTO "{table.name}" ({columns_sql}) SELECT {columns_sql} FROM "{temp_table_name}"'))
        connection.execute(text(f'DROP TABLE "{temp_table_name}"'))

    def _get_sqlite_table_columns(self, connection: Any, table_name: str) -> list[str]:
        table_exists = (
            connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name",
                {"table_name": table_name},
            )
            .scalars()
            .first()
        )
        if table_exists is None:
            return []

        return [row[1] for row in connection.execute(text(f"PRAGMA table_info({table_name})")).all()]

    def _render_sqlite_column(self, column: Any) -> str:
        rendered_column = str(CreateColumn(column).compile(dialect=self._engine.dialect))
        if "PRIMARY KEY" in rendered_column:
            msg = f"Cannot add primary key column via ALTER TABLE: {column.name}"
            raise ValueError(msg)
        return rendered_column


def build_sqlite_url(db_path: Path) -> str:
    """Строит SQLAlchemy URL для SQLite-файла."""

    return f"sqlite:///{db_path}"
