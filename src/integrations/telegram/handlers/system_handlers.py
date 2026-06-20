from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import format_chatid, format_whoami
from src.integrations.telegram.messages import MenuMessages
from src.integrations.telegram.ui.menu.guest_menu import build_guest_menu
from src.integrations.telegram.ui.menu.system_menu import build_system_menu
from src.services.system_status.system_status_service import SystemStatusService
from src.storage.orm import AllowedUser
from src.storage.orm.system.audit_log import AuditLog


class SystemHandlers:
    """Обрабатывает системные команды Telegram-бота."""

    def __init__(self, telegram: TelegramClient, audit_log: type[AuditLog]) -> None:
        self.telegram = telegram
        self.audit_log = audit_log

    def easy_start(self, telegram_id: int) -> None:
        self.telegram.send_message(
            telegram_id,
            MenuMessages.System.ONBOARDING,
            reply_markup=build_system_menu(is_owner=AllowedUser.is_owner(telegram_id)),
        )

    def whoami(self, telegram_id: int | None, username: str | None) -> None:
        if telegram_id is None:
            return
        reply_markup = build_system_menu(is_owner=AllowedUser.is_owner(telegram_id)) if AllowedUser.exists(telegram_id) else build_guest_menu()
        self.telegram.send_message(telegram_id, format_whoami(telegram_id, username), reply_markup=reply_markup)

    def readiness(self, telegram_id: int) -> None:
        status = SystemStatusService.get_status(telegram_id)
        lines = [
            f"{'✅' if status.company and status.bank_details else '❌'} Профиль (компания + реквизиты)",
            f"{'✅' if status.signature else '❌'} Подпись",
            f"{'✅' if status.gmail else '❌'} Gmail",
            f"{'✅' if status.invoice_available else '❌'} Инвойс (профиль + подпись)",
            f"{'✅' if status.bank_confirmation_available and status.signature and status.gmail else '❌'} "
            f"Банковский день (профиль + подпись + Gmail)",
        ]
        text = "✅ Готовность к работе\n\n" + "\n".join(lines)
        self.telegram.send_message(
            telegram_id,
            text,
            reply_markup=build_system_menu(is_owner=AllowedUser.is_owner(telegram_id)),
        )

    def chatid(self, telegram_id: int | None) -> None:
        if telegram_id is None:
            return
        self.telegram.send_message(
            telegram_id, format_chatid(telegram_id), reply_markup=build_system_menu(is_owner=AllowedUser.is_owner(telegram_id))
        )
