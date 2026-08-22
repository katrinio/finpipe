"""Telegram UI button constants."""

from src.integrations.telegram.buttons.documents import DocumentsMenuButtons
from src.integrations.telegram.buttons.invoice import InvoiceButtons, InvoiceMenuButtons
from src.integrations.telegram.buttons.main_menu import MainMenuButtons
from src.integrations.telegram.buttons.navigation import NavigationButtons
from src.integrations.telegram.buttons.profile import ProfileButtons
from src.integrations.telegram.buttons.signature import SignatureButtons
from src.integrations.telegram.buttons.system import SystemButtons

__all__ = [
    "DocumentsMenuButtons",
    "InvoiceButtons",
    "InvoiceMenuButtons",
    "MainMenuButtons",
    "NavigationButtons",
    "ProfileButtons",
    "SignatureButtons",
    "SystemButtons",
]
