"""Хранение обработанных Telegram update_id в SQLite."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.storage.database import Database, build_sqlite_url
from src.storage.orm import TelegramUpdate


class TelegramUpdateStorage:
    """Хранит и проверяет обработанные Telegram update_id."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def get_last_processed_update_id(self) -> int | None:
        """Возвращает последний обработанный update_id или `None`."""

        with self._session_factory() as session:
            return TelegramUpdate.get_last_primary_key(session)

    def mark_processed(self, update_id: int) -> None:
        """Помечает update_id обработанным без дубликатов."""

        with self._session_factory() as session:
            TelegramUpdate.add_by_primary_key(session, update_id)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()


def build_telegram_update_storage(db_path: Path) -> TelegramUpdateStorage:
    """Создаёт storage для Telegram update_id на существующей SQLite-базе."""

    database = Database(build_sqlite_url(db_path))
    database.initialize_schema()
    return TelegramUpdateStorage(database.session)
