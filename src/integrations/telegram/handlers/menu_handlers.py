from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.ui.buttons import IntegrationsButtons, MainMenuButtons, ProfileButtons
from src.integrations.telegram.ui.menu.document_menu import build_document_menu
from src.integrations.telegram.ui.menu.integration_menu import build_gmail_menu, build_integration_menu
from src.integrations.telegram.ui.menu.menu import build_main_menu
from src.integrations.telegram.ui.menu.profile_menu import build_profile_menu, build_signature_menu
from src.integrations.telegram.ui.menu.system_menu import build_system_menu


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
            IntegrationsButtons.GMAIL,
            reply_markup=build_gmail_menu(),
        )

    def signature_menu(self) -> None:
        self.telegram.send_message(
            ProfileButtons.SIGNATURE,
            reply_markup=build_signature_menu(),
        )

    def settings_menu(self) -> None:
        self.telegram.send_message(
            MainMenuButtons.PROFILE,
            reply_markup=build_profile_menu(),
        )

    def document_menu(self) -> None:
        self.telegram.send_message(
            MainMenuButtons.DOCUMENTS,
            reply_markup=build_document_menu(),
        )

    def integration_menu(self) -> None:
        self.telegram.send_message(
            MainMenuButtons.INTEGRATIONS,
            reply_markup=build_integration_menu(),
        )
