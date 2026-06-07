"""Репозиторий истории инвойсов."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.storage.orm import HistoryRecord


class InvoiceHistoryRepository(Protocol):
    """Репозиторий истории инвойсов с бизнес-операциями по номерам инвойсов."""

    def list_invoices(self) -> list[str]:
        """Возвращает все номера инвойсов в отсортированном виде."""

    def invoice_exists(self, invoice_number: str) -> bool:
        """Проверяет наличие инвойса по его бизнес-идентификатору."""

    def add_invoice(self, invoice_number: str) -> None:
        """Сохраняет номер инвойса, если он ещё не был записан."""

    def get_last_invoice(self) -> str | None:
        """Возвращает максимальный номер инвойса или `None`, если записей нет."""


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
