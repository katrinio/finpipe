"""Gmail integration modules."""

from .auth import get_gmail_service
from .gmail_models import BankEmail
from .search import find_bank_email

__all__ = [
    "BankEmail",
    "find_bank_email",
    "get_gmail_service",
]
