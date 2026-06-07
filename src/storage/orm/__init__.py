"""ORM-сущности и base для storage-слоя."""

from src.storage.orm.base import BaseStorage
from src.storage.orm.history_record import HistoryRecord
from src.storage.orm.processed_message import ProcessedMessage
from src.storage.orm.telegram_updates import TelegramUpdate

__all__ = [
    "BaseStorage",
    "HistoryRecord",
    "ProcessedMessage",
    "TelegramUpdate",
]
