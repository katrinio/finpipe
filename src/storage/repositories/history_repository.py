"""Репозиторий истории инвойсов."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

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
            return HistoryRecord.list_primary_keys(session)

    def invoice_exists(self, invoice_number: str) -> bool:
        """Проверяет существование номера инвойса."""

        with self._session_factory() as session:
            return HistoryRecord.exists_by_primary_key(session, invoice_number)

    def add_invoice(self, invoice_number: str) -> None:
        """Сохраняет номер инвойса без дублирования."""

        with self._session_factory() as session:
            HistoryRecord.add_by_primary_key(session, invoice_number)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()

    def get_last_invoice(self) -> str | None:
        """Возвращает последний номер инвойса согласно текущему бизнес-порядку."""

        with self._session_factory() as session:
            return HistoryRecord.get_last_primary_key(session)
