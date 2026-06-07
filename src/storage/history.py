"""Совместимый фасад истории инвойсов поверх нового repository-слоя."""

from __future__ import annotations

import logging

from src.constants import Dir
from src.storage.dependencies import build_storage_dependencies
from src.storage.repositories import InvoiceHistoryRepository

LOGGER = logging.getLogger(__name__)


class HistoryStorage:
    """Сохраняет прежний публичный API и делегирует операции репозиторию истории инвойсов."""

    FILE_PATH = Dir.STORAGE_HISTORY_JSON
    DB_PATH = Dir.STORAGE_DB

    @classmethod
    def _repository(cls) -> InvoiceHistoryRepository:
        return build_storage_dependencies(
            db_path=cls.DB_PATH,
            history_json_path=cls.FILE_PATH,
        ).invoice_history

    @classmethod
    def load_history(cls) -> set[str]:
        """Загружает набор уже сохранённых номеров инвойсов."""

        return set(cls._repository().list_invoices())

    @classmethod
    def invoice_exists(cls, invoice_number: str) -> bool:
        """Проверяет, был ли инвойс с таким номером уже создан."""

        return cls._repository().invoice_exists(invoice_number)

    @classmethod
    def add_invoice(cls, invoice_number: str) -> None:
        """Добавляет номер инвойса в историю."""

        cls._repository().add_invoice(invoice_number)
        LOGGER.info("Saved invoice %s", invoice_number)

    @classmethod
    def list_invoices(cls) -> list[str]:
        """Возвращает отсортированный список номеров инвойсов."""

        return cls._repository().list_invoices()

    @classmethod
    def get_last_invoice(cls) -> str | None:
        """Возвращает последний номер инвойса или `None`."""

        return cls._repository().get_last_invoice()
