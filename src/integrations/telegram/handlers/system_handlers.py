from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import format_chatid, format_whoami
from src.integrations.telegram.messages import MenuMessages, MsgIcon
from src.integrations.telegram.ui.menu.profile_menu import build_profile_menu
from src.integrations.telegram.ui.menu.system_menu import build_system_menu
from src.services.system_status.system_status_service import SystemStatusService


class SystemHandlers:
    """Обрабатывает системные команды Telegram-бота."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def easy_start(self, telegram_id: int) -> None:
        self.telegram.send_message(
            telegram_id,
            MenuMessages.System.ONBOARDING,
            reply_markup=build_system_menu(),
        )

    def whoami(self, telegram_id: int | None, username: str | None) -> None:
        if telegram_id is None:
            return
        self.telegram.send_message(telegram_id, format_whoami(telegram_id, username), reply_markup=build_profile_menu())

    def readiness(self, telegram_id: int) -> None:
        status = SystemStatusService.get_status(telegram_id)
        lines = [
            f"{MsgIcon.status(status.company and status.bank_details)} Профиль (компания + реквизиты)",
            f"{MsgIcon.status(status.signature)} Подпись",
            f"{MsgIcon.status(status.invoice_available)} Инвойс (профиль + подпись)",
        ]
        text = "✅ Готовность к работе\n\n" + "\n".join(lines)
        self.telegram.send_message(
            telegram_id,
            text,
            reply_markup=build_system_menu(),
        )

    def chatid(self, telegram_id: int | None) -> None:
        if telegram_id is None:
            return
        self.telegram.send_message(telegram_id, format_chatid(telegram_id), reply_markup=build_system_menu())
