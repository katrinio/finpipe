"""Базовый declarative class для ORM storage-слоя."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from src.storage.database import Database


class BaseStorage(DeclarativeBase):
    """Общий SQLAlchemy base для всех storage-сущностей."""


class BaseModel(BaseStorage):
    """Базовый класс для простых таблиц с операциями по первичному ключу."""

    __abstract__ = True
    __pk_column_name__: ClassVar[str]

    database: ClassVar["Database"]
