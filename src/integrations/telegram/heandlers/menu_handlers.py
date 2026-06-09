from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.ui.buttons import MainMenuButtons
from src.integrations.telegram.ui.menu import (
    build_gmail_menu,
    build_main_menu,
    build_signature_menu,
    build_system_menu,
)


class MenuHandler:
    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def main_menu(self) -> None:
        self.telegram.send_message(
            "🏠 Главное меню",
            reply_markup=build_main_menu(),
        )

    def system_menu(self) -> None:
        self.telegram.send_message(
            MainMenuButtons.SYSTEM,
            reply_markup=build_system_menu(),
        )

    def gmail_menu(self) -> None:
        self.telegram.send_message(
            MainMenuButtons.GMAIL,
            reply_markup=build_gmail_menu(),
        )

    def signature_menu(self) -> None:
        self.telegram.send_message(
            MainMenuButtons.SIGNATURE,
            reply_markup=build_signature_menu(),
        )
