"""Backward-compatible re-export of Telegram message constants."""

from src.integrations.telegram.messages import (
    BankMessages,
    CommonMessages,
    InvoiceMessages,
    MenuMessages,
    MsgIcon,
    ProfileMessages,
    SignatureMessages,
)

__all__ = [
    "BankMessages",
    "CommonMessages",
    "InvoiceMessages",
    "MenuMessages",
    "MsgIcon",
    "ProfileMessages",
    "SignatureMessages",
]
