"""Репозиторий обработанных банковских писем."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.storage.orm import ProcessedMessage


class ProcessedMessageRepository(Protocol):
    """Репозиторий истории обработанных банковских писем."""

    def list_message_ids(self) -> list[str]:
        """Возвращает все обработанные message id в отсортированном виде."""

    def is_processed(self, message_id: str) -> bool:
        """Проверяет, было ли письмо уже обработано."""

    def mark_as_processed(self, message_id: str) -> None:
        """Помечает письмо как обработанное без создания дубликатов."""

    def replace_all(self, message_ids: set[str]) -> None:
        """Полностью заменяет набор обработанных писем новым значением."""

    def clear(self) -> None:
        """Очищает историю обработанных писем."""


class SQLAlchemyProcessedMessageRepository(ProcessedMessageRepository):
    """Работает с ORM-моделью обработанных писем банка."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def list_message_ids(self) -> list[str]:
        """Возвращает отсортированный список обработанных message id."""

        with self._session_factory() as session:
            return ProcessedMessage.list_primary_keys(session)

    def is_processed(self, message_id: str) -> bool:
        """Проверяет наличие письма в таблице обработанных."""

        with self._session_factory() as session:
            return ProcessedMessage.exists_by_primary_key(session, message_id)

    def mark_as_processed(self, message_id: str) -> None:
        """Добавляет письмо в историю без создания дубликатов."""

        with self._session_factory() as session:
            ProcessedMessage.add_by_primary_key(session, message_id)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()

    def replace_all(self, message_ids: set[str]) -> None:
        """Полностью заменяет содержимое таблицы обработанных писем."""

        with self._session_factory() as session:
            ProcessedMessage.replace_primary_keys(session, sorted(message_ids))
            session.commit()

    def clear(self) -> None:
        """Удаляет все записи об обработанных письмах."""

        with self._session_factory() as session:
            ProcessedMessage.clear(session)
            session.commit()
