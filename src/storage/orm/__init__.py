"""ORM-сущности и base для storage-слоя."""

from src.storage.orm.system.audit_log import AuditLog
from src.storage.orm.system.document_generation_history import (
    DocumentGenerationHistory,
    DocumentGenerationStatus,
    DocumentType,
)
from src.storage.orm.system.known_user import KnownUser
from src.storage.orm.system.oauth_session import OAuthSession
from src.storage.orm.system.processed_message import ProcessedMessage
from src.storage.orm.system.telegram_update import TelegramUpdate
from src.storage.orm.system.user_state_storage import UserStateStorage
from src.storage.orm.user.allowed_user import AllowedUser, UserRole
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.storage.orm.user.gmail_account import GmailAccount
from src.storage.orm.user.signature import Signature
from src.storage.orm.user.user_config import UserConfig

__all__ = [
    "AllowedUser",
    "AuditLog",
    "BankDetails",
    "CompanyProfile",
    "DocumentGenerationHistory",
    "DocumentGenerationStatus",
    "DocumentType",
    "GmailAccount",
    "KnownUser",
    "OAuthSession",
    "ProcessedMessage",
    "Signature",
    "TelegramUpdate",
    "UserConfig",
    "UserRole",
    "UserStateStorage",
]
