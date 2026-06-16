from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.messages import MenuMessages
from src.integrations.telegram.ui.buttons import (
    DocumentsMenuButtons,
    IntegrationsButtons,
    MainMenuButtons,
    NavigationButtons,
    OwnerButtons,
    ProfileButtons,
)
from src.integrations.telegram.ui.menu.admin_menu import build_admin_menu, build_users_menu
from src.integrations.telegram.ui.menu.document_menu import build_conversion_order_menu, build_document_menu, build_invoice_menu
from src.integrations.telegram.ui.menu.integration_menu import build_gmail_menu, build_integration_menu
from src.integrations.telegram.ui.menu.menu import build_main_menu
from src.integrations.telegram.ui.menu.profile_menu import build_profile_menu, build_signature_menu
from src.integrations.telegram.ui.menu.system_menu import build_system_menu
from src.integrations.telegram.ui.messages import CommonMessages
from src.storage.orm import AllowedUser


class MenuHandler:
    """Отправляет экраны и меню Telegram-бота."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def main_start(self, telegram_id: int) -> None:
        """Показывает стартовый экран бота."""

        self.telegram.send_message(
            telegram_id,
            CommonMessages.General.WELCOME,
            reply_markup=build_main_menu(is_owner=AllowedUser.is_owner(telegram_id)),
        )

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
            IntegrationsButtons.GMAIL,
            reply_markup=build_gmail_menu(),
        )

    def signature_menu(self, telegram_id: int) -> None:
        """Открывает раздел управления подписью."""

        self.telegram.send_message(
            telegram_id,
            ProfileButtons.SIGNATURE,
            reply_markup=build_signature_menu(),
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
        """Открывает подменю работы с Salary Invoice."""

        self.telegram.send_message(
            telegram_id,
            DocumentsMenuButtons.SALARY_INVOICE,
            reply_markup=build_invoice_menu(),
        )

    def conversion_order_menu(self, telegram_id: int) -> None:
        self.telegram.send_message(
            telegram_id,
            DocumentsMenuButtons.CONVERSION_ORDER,
            reply_markup=build_conversion_order_menu(),
        )

    def integration_menu(self, telegram_id: int) -> None:
        """Открывает раздел интеграций."""

        self.telegram.send_message(
            telegram_id,
            MainMenuButtons.INTEGRATIONS,
            reply_markup=build_integration_menu(),
        )

    def admin_menu(self, telegram_id: int) -> None:
        """Открывает раздел админа (доступен только овнеру)."""

        self.telegram.send_message(
            telegram_id,
            OwnerButtons.ADMIN_PANEL,
            reply_markup=build_admin_menu(),
        )

    def user_menu(self, telegram_id: int) -> None:
        """Открывает раздел админа (доступен только овнеру)."""

        self.telegram.send_message(
            telegram_id,
            OwnerButtons.USERS,
            reply_markup=build_users_menu(),
        )
