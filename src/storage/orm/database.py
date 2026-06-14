"""Настройка SQLAlchemy engine и session factory."""

import logging
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.storage.config import DatabaseConfig
from src.storage.orm.base import BaseModel

LOGGER = logging.getLogger(__name__)


class Database:
    """Инкапсулирует engine и фабрику сессий для persistence-слоя."""

    def __init__(self, database_url: str, echo: bool = False) -> None:
        self._database_url = database_url
        self._engine = create_engine(database_url, echo=echo, future=True)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False, class_=Session)

    @classmethod
    def from_env(cls, echo: bool = False) -> "Database":
        """Creates a database instance from DATABASE_URL."""

        return cls(DatabaseConfig.get_database_url(), echo=echo)

    @property
    def engine(self) -> Engine:
        """Возвращает SQLAlchemy engine."""

        return self._engine

    @property
    def database_url(self) -> str:
        """Returns the configured database URL."""

        return self._database_url

    def bind_models(self) -> None:
        """Привязывает ORM-модели к engine без создания или изменения схемы."""

        BaseModel.database = self

    def session(self) -> Session:
        """Создаёт новую независимую сессию."""

        return self._session_factory()


def build_sqlite_url(db_path: Path) -> str:
    """Legacy helper kept for test fixtures that still create temporary SQLite databases."""

    return f"sqlite:///{db_path}"
