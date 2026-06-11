"""Базовый declarative class для ORM storage-слоя."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy.orm import DeclarativeBase, Session

if TYPE_CHECKING:
    from src.storage.orm.database import Database


class BaseModel(DeclarativeBase):
    """Базовый класс для простых таблиц с операциями по первичному ключу."""

    __abstract__ = True
    __pk_column_name__: ClassVar[str]

    database: ClassVar["Database"]

    @classmethod
    @contextmanager
    def session(cls) -> Generator[Session]:
        with cls.database.session() as session:
            yield session
