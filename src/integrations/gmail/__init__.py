"""Интеграция с Gmail для поиска и загрузки писем банка."""

from .auth import get_gmail_service
from .gmail_models import BankEmail
from .gmail_sender import GmailSender, send_email
from .search import find_bank_email

__all__ = [
    "BankEmail",
    "GmailSender",
    "find_bank_email",
    "get_gmail_service",
    "send_email",
]
