from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.ui.buttons import IntegrationsButtons, MainMenuButtons, NavigationButtons, ProfileButtons
from src.integrations.telegram.ui.menu.document_menu import build_document_menu
from src.integrations.telegram.ui.menu.integration_menu import build_gmail_menu, build_integration_menu
from src.integrations.telegram.ui.menu.menu import build_main_menu
from src.integrations.telegram.ui.menu.profile_menu import build_profile_menu, build_signature_menu
from src.integrations.telegram.ui.menu.system_menu import build_system_menu
from src.integrations.telegram.ui.messages import CommonMessages


class MenuHandler:
    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def main_start(self, telegram_id: int) -> None:
        self.telegram.send_message(
            telegram_id,
            CommonMessages.WELCOME,
            reply_markup=build_main_menu(),
        )

    def main_menu(self, telegram_id: int) -> None:
        self.telegram.send_message(
            telegram_id,
            NavigationButtons.HOME,
            reply_markup=build_main_menu(),
        )

    def system_menu(self, telegram_id: int) -> None:
        self.telegram.send_message(
            telegram_id,
            MainMenuButtons.SYSTEM,
            reply_markup=build_system_menu(),
        )

    def gmail_menu(self, telegram_id: int) -> None:
        self.telegram.send_message(
            telegram_id,
            IntegrationsButtons.GMAIL,
            reply_markup=build_gmail_menu(),
        )

    def signature_menu(self, telegram_id: int) -> None:
        self.telegram.send_message(
            telegram_id,
            ProfileButtons.SIGNATURE,
            reply_markup=build_signature_menu(),
        )

    def settings_menu(self, telegram_id: int) -> None:
        self.telegram.send_message(
            telegram_id,
            MainMenuButtons.PROFILE,
            reply_markup=build_profile_menu(),
        )

    def document_menu(self, telegram_id: int) -> None:
        self.telegram.send_message(
            telegram_id,
            MainMenuButtons.DOCUMENTS,
            reply_markup=build_document_menu(),
        )

    def integration_menu(self, telegram_id: int) -> None:
        self.telegram.send_message(
            telegram_id,
            MainMenuButtons.INTEGRATIONS,
            reply_markup=build_integration_menu(),
        )
