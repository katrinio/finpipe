"""Базовый declarative class для ORM storage-слоя."""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from typing import Any, ClassVar

from sqlalchemy import delete, select
from sqlalchemy.orm import DeclarativeBase, Session


class BaseStorage(DeclarativeBase):
    """Общий SQLAlchemy base для всех storage-сущностей."""


class BaseModel(BaseStorage):
    """Базовый класс для простых таблиц с операциями по первичному ключу."""

    __abstract__ = True
    __pk_column_name__: ClassVar[str]

    database: Any

    @classmethod
    @contextmanager
    def session(cls):
        with cls.database.session() as session:
            yield session

    @classmethod
    def _pk_column(cls) -> Any:
        """Возвращает колонку первичного ключа таблицы."""

        return getattr(cls, cls.__pk_column_name__)

    @classmethod
    def list_primary_keys(cls, session: Session) -> list[Any]:
        """Возвращает все значения первичного ключа в отсортированном виде."""

        statement = select(cls._pk_column()).order_by(cls._pk_column())
        return list(session.scalars(statement))

    @classmethod
    def exists_by_primary_key(cls, session: Session, value: Any) -> bool:
        """Проверяет наличие строки по первичному ключу."""

        statement = select(cls._pk_column()).where(cls._pk_column() == value).limit(1)
        return session.scalar(statement) is not None

    @classmethod
    def get_last_primary_key(cls, session: Session) -> Any | None:
        """Возвращает наибольшее значение первичного ключа или `None`."""

        statement = select(cls._pk_column()).order_by(cls._pk_column().desc()).limit(1)
        return session.scalar(statement)

    @classmethod
    def add_by_primary_key(cls, session: Session, value: Any) -> None:
        """Добавляет строку с заданным первичным ключом."""

        session.add(cls(**{cls.__pk_column_name__: value}))

    @classmethod
    def replace_primary_keys(cls, session: Session, values: Iterable[Any]) -> None:
        """Полностью заменяет содержимое таблицы значениями первичного ключа."""

        session.execute(delete(cls))
        session.add_all(cls(**{cls.__pk_column_name__: value}) for value in values)

    @classmethod
    def clear(cls, session: Session) -> None:
        """Удаляет все строки таблицы."""

        session.execute(delete(cls))
