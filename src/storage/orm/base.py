"""Базовый declarative class для ORM storage-слоя."""

from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
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


def current_utc_timestamp() -> datetime:
    """Возвращает UTC-время без микросекунд для ORM-полей."""

    return datetime.now(UTC).replace(microsecond=0)


def normalize_timestamp(value: datetime) -> datetime:
    """Обрезает микросекунды у внешнего datetime перед сохранением."""

    return value.replace(microsecond=0)
