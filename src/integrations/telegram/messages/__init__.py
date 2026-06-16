"""Telegram UI message constants."""

from src.integrations.telegram.messages.audit import AuditLogMessages
from src.integrations.telegram.messages.bank import BankMessages
from src.integrations.telegram.messages.common import CommonMessages, Msg
from src.integrations.telegram.messages.gmail import GmailMessages
from src.integrations.telegram.messages.invoice import InvoiceMessages
from src.integrations.telegram.messages.menu import ConversionOrderMessages, MenuMessages
from src.integrations.telegram.messages.owner import OwnerMessages
from src.integrations.telegram.messages.profile import ProfileMessages
from src.integrations.telegram.messages.signature import SignatureMessages

__all__ = [
    "AuditLogMessages",
    "BankMessages",
    "CommonMessages",
    "ConversionOrderMessages",
    "GmailMessages",
    "InvoiceMessages",
    "MenuMessages",
    "Msg",
    "OwnerMessages",
    "ProfileMessages",
    "SignatureMessages",
]
