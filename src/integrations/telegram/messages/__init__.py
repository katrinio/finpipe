"""Telegram UI message constants."""

from src.integrations.telegram.messages.audit import AuditLogMessages, AuditLogMessagesV2
from src.integrations.telegram.messages.bank import BankMessages, BankMessagesV2, ConversionOrderMessages
from src.integrations.telegram.messages.common import CommonMessages, CommonMessagesV2, Msg
from src.integrations.telegram.messages.gmail import GmailMessages, GmailMessagesV2
from src.integrations.telegram.messages.invoice import InvoiceMessages, InvoiceMessagesV2
from src.integrations.telegram.messages.menu import ConversionOrderMessagesV2, MenuMessages, MenuMessagesV2
from src.integrations.telegram.messages.owner import OwnerMessages, OwnerMessagesV2
from src.integrations.telegram.messages.profile import ProfileMessages, ProfileMessageV2
from src.integrations.telegram.messages.signature import SignatureMessages, SignatureMessagesV2

__all__ = [
    "AuditLogMessages",
    "AuditLogMessagesV2",
    "BankMessages",
    "BankMessagesV2",
    "CommonMessages",
    "CommonMessagesV2",
    "ConversionOrderMessages",
    "ConversionOrderMessagesV2",
    "GmailMessages",
    "GmailMessagesV2",
    "InvoiceMessages",
    "InvoiceMessagesV2",
    "MenuMessages",
    "MenuMessagesV2",
    "Msg",
    "OwnerMessages",
    "OwnerMessagesV2",
    "ProfileMessageV2",
    "ProfileMessages",
    "SignatureMessages",
    "SignatureMessagesV2",
]
