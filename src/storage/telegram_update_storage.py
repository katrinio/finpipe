"""Хранение обработанных Telegram update_id в SQLite."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.storage.database import Database, build_sqlite_url
from src.storage.orm import TelegramUpdate


class TelegramUpdateStorage:
    """Хранит и проверяет обработанные Telegram update_id."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def is_processed(self, update_id: int) -> bool:
        """Проверяет, был ли update_id уже обработан."""

        with self._session_factory() as session:
            statement = select(TelegramUpdate.update_id).where(TelegramUpdate.update_id == update_id).limit(1)
            return session.scalar(statement) is not None

    def get_last_processed_update_id(self) -> int | None:
        """Возвращает последний обработанный update_id или `None`."""

        with self._session_factory() as session:
            statement = select(func.max(TelegramUpdate.update_id))
            return session.scalar(statement)

    def mark_processed(self, update_id: int) -> None:
        """Помечает update_id обработанным без дубликатов."""

        with self._session_factory() as session:
            session.add(TelegramUpdate(update_id=update_id))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()


def build_telegram_update_storage(db_path: Path) -> TelegramUpdateStorage:
    """Создаёт storage для Telegram update_id на существующей SQLite-базе."""

    database = Database(build_sqlite_url(db_path))
    database.initialize_schema()
    return TelegramUpdateStorage(database.session)
