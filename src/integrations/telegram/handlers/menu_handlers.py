from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.messages import MenuMessages
from src.integrations.telegram.ui.buttons import (
    DocumentsMenuButtons,
    MainMenuButtons,
    NavigationButtons,
    OwnerButtons,
)
from src.integrations.telegram.ui.menu.admin_menu import build_users_menu
from src.integrations.telegram.ui.menu.document_menu import (
    build_document_menu,
    build_invoice_menu,
)
from src.integrations.telegram.ui.menu.integration_menu import build_gmail_menu
from src.integrations.telegram.ui.menu.menu import build_main_menu
from src.integrations.telegram.ui.menu.profile_menu import build_profile_menu
from src.integrations.telegram.ui.menu.system_menu import build_system_menu
from src.storage.orm import AllowedUser
from src.storage.orm.user.user_config import UserConfig


class MenuHandler:
    """Отправляет экраны и меню Telegram-бота."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def main_start(self, telegram_id: int) -> None:
        """Показывает стартовый экран бота."""

        config = UserConfig.get_or_create(telegram_id)
        if not config.onboarding_shown:
            self.telegram.send_message(
                telegram_id,
                MenuMessages.System.ONBOARDING,
                reply_markup=build_main_menu(is_owner=AllowedUser.is_owner(telegram_id)),
            )
            UserConfig.mark_onboarding_shown(telegram_id)

        self.main_menu(telegram_id)

    def main_menu(self, telegram_id: int, onboarding: bool = False) -> None:
        """Открывает главное меню."""

        if not onboarding:
            self.telegram.send_message(
                telegram_id,
                NavigationButtons.HOME,
                reply_markup=build_main_menu(is_owner=AllowedUser.is_owner(telegram_id)),
            )
        else:
            self.telegram.send_message(
                telegram_id,
                MenuMessages.System.ONBOARDING,
                reply_markup=build_main_menu(is_owner=AllowedUser.is_owner(telegram_id)),
            )

    def system_menu(self, telegram_id: int) -> None:
        """Открывает раздел системных команд."""

        self.telegram.send_message(
            telegram_id,
            MainMenuButtons.SYSTEM,
            reply_markup=build_system_menu(is_owner=AllowedUser.is_owner(telegram_id)),
        )

    def gmail_menu(self, telegram_id: int) -> None:
        """Открывает раздел Gmail-интеграции."""

        self.telegram.send_message(
            telegram_id,
            MainMenuButtons.INTEGRATIONS,
            reply_markup=build_gmail_menu(),
        )

    def settings_menu(self, telegram_id: int) -> None:
        """Открывает раздел профиля пользователя."""

        self.telegram.send_message(
            telegram_id,
            MainMenuButtons.PROFILE,
            reply_markup=build_profile_menu(),
        )

    def document_menu(self, telegram_id: int) -> None:
        """Открывает раздел документных workflow."""

        self.telegram.send_message(
            telegram_id,
            MainMenuButtons.DOCUMENTS,
            reply_markup=build_document_menu(),
        )

    def invoice_menu(self, telegram_id: int) -> None:
        """Открывает подменю работы с инвойсом."""

        self.telegram.send_message(
            telegram_id,
            DocumentsMenuButtons.SALARY_INVOICE,
            reply_markup=build_invoice_menu(),
        )

    def user_menu(self, telegram_id: int) -> None:
        """Открывает раздел администрирования пользователей."""

        self.telegram.send_message(
            telegram_id,
            OwnerButtons.USERS,
            reply_markup=build_users_menu(),
        )
