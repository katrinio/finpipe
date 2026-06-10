"""ORM-сущности и base для storage-слоя."""

from src.storage.orm.system.audit_log import AuditLog
from src.storage.orm.system.history_record import HistoryRecord
from src.storage.orm.system.oauth_session import OAuthSession
from src.storage.orm.system.processed_message import ProcessedMessage
from src.storage.orm.system.telegram_update import TelegramUpdate
from src.storage.orm.system.user_state_storage import UserStateStorage
from src.storage.orm.user.allowed_user import AllowedUser
from src.storage.orm.user.signature import Signature
from src.storage.orm.user.user_config import UserConfig

__all__ = [
    "AllowedUser",
    "AuditLog",
    "HistoryRecord",
    "OAuthSession",
    "ProcessedMessage",
    "Signature",
    "TelegramUpdate",
    "UserConfig",
    "UserStateStorage",
]
