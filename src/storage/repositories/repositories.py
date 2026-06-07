"""Абстракции репозиториев для локального постоянного хранилища."""

from __future__ import annotations

from typing import Protocol


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
