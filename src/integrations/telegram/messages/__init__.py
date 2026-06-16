"""Telegram UI message constants."""

from src.integrations.telegram.messages.audit_messages import AuditLogMessages
from src.integrations.telegram.messages.bank_messages import BankMessages
from src.integrations.telegram.messages.common_messages import CommonMessages, Msg
from src.integrations.telegram.messages.gmail_messages import GmailMessages
from src.integrations.telegram.messages.invoice_messages import InvoiceMessages
from src.integrations.telegram.messages.menu_messages import ConversionOrderMessages, MenuMessages
from src.integrations.telegram.messages.owner_messages import OwnerMessages
from src.integrations.telegram.messages.profile_messages import ProfileMessages
from src.integrations.telegram.messages.signature_messages import SignatureMessages

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
