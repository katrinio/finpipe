"""Интеграция с Gmail для поиска и загрузки писем банка."""

__all__ = [
    "BankEmail",
    "GmailAccountService",
    "GmailAccountStatus",
    "GmailOAuth",
    "GmailOAuthCallbackService",
    "GmailOAuthResult",
    "GmailOAuthSettings",
    "GmailSender",
    "OAuthCallbackResult",
    "find_bank_email",
    "get_gmail_service",
    "send_email",
]

from src.integrations.gmail.account_service import GmailAccountService, GmailAccountStatus
from src.integrations.gmail.auth import get_gmail_service
from src.integrations.gmail.gmail_models import BankEmail
from src.integrations.gmail.gmail_oauth import GmailOAuth, GmailOAuthResult
from src.integrations.gmail.gmail_sender import GmailSender, send_email
from src.integrations.gmail.oauth_callback import GmailOAuthCallbackService, OAuthCallbackResult
from src.integrations.gmail.search import find_bank_email
from src.integrations.gmail.settings import GmailOAuthSettings


def __getattr__(name: str) -> object:
    if name == "BankEmail":
        from .gmail_models import BankEmail

        return BankEmail
    if name in {"GmailAccountService", "GmailAccountStatus"}:
        from .account_service import GmailAccountService, GmailAccountStatus

        return {"GmailAccountService": GmailAccountService, "GmailAccountStatus": GmailAccountStatus}[name]
    if name == "get_gmail_service":
        from .auth import get_gmail_service

        return get_gmail_service
    if name in {"GmailOAuth", "GmailOAuthResult"}:
        from .gmail_oauth import GmailOAuth, GmailOAuthResult

        return {"GmailOAuth": GmailOAuth, "GmailOAuthResult": GmailOAuthResult}[name]
    if name in {"GmailSender", "send_email"}:
        from .gmail_sender import GmailSender, send_email

        return {"GmailSender": GmailSender, "send_email": send_email}[name]
    if name in {"GmailOAuthCallbackService", "OAuthCallbackResult"}:
        from .oauth_callback import GmailOAuthCallbackService, OAuthCallbackResult

        return {"GmailOAuthCallbackService": GmailOAuthCallbackService, "OAuthCallbackResult": OAuthCallbackResult}[name]
    if name == "find_bank_email":
        from .search import find_bank_email

        return find_bank_email
    if name == "GmailOAuthSettings":
        from .settings import GmailOAuthSettings

        return GmailOAuthSettings
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
