"""Интеграция с Gmail для поиска и загрузки писем банка."""

from .account_service import GmailAccountService, GmailAccountStatus
from .auth import get_gmail_service
from .gmail_models import BankEmail
from .gmail_oauth import GmailOAuth, GmailOAuthResult
from .gmail_sender import GmailSender, send_email
from .oauth_callback import GmailOAuthCallbackService, OAuthCallbackResult
from .search import find_bank_email
from .settings import GmailOAuthSettings

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
