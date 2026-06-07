"""SQLAlchemy-реализация локальных репозиториев."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.storage.orm import HistoryRecord, ProcessedMessage
from src.storage.repositories import InvoiceHistoryRepository, ProcessedMessageRepository


class SQLAlchemyInvoiceHistoryRepository(InvoiceHistoryRepository):
    """Работает с ORM-моделью истории инвойсов и скрывает SQLAlchemy от приложения."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def list_invoices(self) -> list[str]:
        """Возвращает номера инвойсов в лексикографическом порядке."""

        with self._session_factory() as session:
            statement = select(HistoryRecord.invoice_number).order_by(HistoryRecord.invoice_number)
            return list(session.scalars(statement))

    def invoice_exists(self, invoice_number: str) -> bool:
        """Проверяет существование номера инвойса."""

        with self._session_factory() as session:
            statement = select(HistoryRecord.invoice_number).where(HistoryRecord.invoice_number == invoice_number).limit(1)
            return session.scalar(statement) is not None

    def add_invoice(self, invoice_number: str) -> None:
        """Сохраняет номер инвойса без дублирования."""

        with self._session_factory() as session:
            session.add(HistoryRecord(invoice_number=invoice_number))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()

    def get_last_invoice(self) -> str | None:
        """Возвращает последний номер инвойса согласно текущему бизнес-порядку."""

        with self._session_factory() as session:
            statement = select(HistoryRecord.invoice_number).order_by(HistoryRecord.invoice_number.desc()).limit(1)
            return session.scalar(statement)


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
