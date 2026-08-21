"""Telegram UI message constants."""

from src.integrations.telegram.messages.common_messages import CommonMessages, MsgIcon
from src.integrations.telegram.messages.invoice_messages import InvoiceMessages
from src.integrations.telegram.messages.menu_messages import MenuMessages
from src.integrations.telegram.messages.owner_messages import OwnerMessages
from src.integrations.telegram.messages.profile_messages import ProfileMessages
from src.integrations.telegram.messages.signature_messages import SignatureMessages

__all__ = [
    "CommonMessages",
    "InvoiceMessages",
    "MenuMessages",
    "MsgIcon",
    "OwnerMessages",
    "ProfileMessages",
    "SignatureMessages",
]
