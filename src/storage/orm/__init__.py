"""ORM-сущности и base для storage-слоя."""

from src.storage.orm.allowed_user import AllowedUser
from src.storage.orm.audit_log import AuditLog
from src.storage.orm.history_record import HistoryRecord
from src.storage.orm.oauth_session import OAuthSession
from src.storage.orm.processed_message import ProcessedMessage
from src.storage.orm.signature import Signature
from src.storage.orm.telegram_update import TelegramUpdate
from src.storage.orm.user_config import UserConfig

__all__ = [
    "AllowedUser",
    "AuditLog",
    "HistoryRecord",
    "OAuthSession",
    "ProcessedMessage",
    "Signature",
    "TelegramUpdate",
    "UserConfig",
]
