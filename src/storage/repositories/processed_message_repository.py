"""Репозиторий обработанных банковских писем."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from sqlalchemy import delete, select
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
            statement = select(ProcessedMessage.message_id).order_by(ProcessedMessage.message_id)
            return list(session.scalars(statement))

    def is_processed(self, message_id: str) -> bool:
        """Проверяет наличие письма в таблице обработанных."""

        with self._session_factory() as session:
            statement = select(ProcessedMessage.message_id).where(ProcessedMessage.message_id == message_id).limit(1)
            return session.scalar(statement) is not None

    def mark_as_processed(self, message_id: str) -> None:
        """Добавляет письмо в историю без создания дубликатов."""

        with self._session_factory() as session:
            session.add(ProcessedMessage(message_id=message_id))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()

    def replace_all(self, message_ids: set[str]) -> None:
        """Полностью заменяет содержимое таблицы обработанных писем."""

        with self._session_factory() as session:
            session.execute(delete(ProcessedMessage))
            session.add_all(ProcessedMessage(message_id=message_id) for message_id in sorted(message_ids))
            session.commit()

    def clear(self) -> None:
        """Удаляет все записи об обработанных письмах."""

        with self._session_factory() as session:
            session.execute(delete(ProcessedMessage))
            session.commit()
