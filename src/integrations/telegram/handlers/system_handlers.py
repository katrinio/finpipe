from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import format_last_action, format_whoami
from src.integrations.telegram.ui.menu.guest_menu import build_guest_menu
from src.integrations.telegram.ui.messages import AuditLogMessagesV2, BotInfo
from src.services.system_status.system_status_service import SystemStatusService
from src.storage.orm.system.audit_log import AuditLog


class SystemHandlers:
    """Обрабатывает системные команды Telegram-бота."""

    def __init__(self, telegram: TelegramClient, audit_log: type[AuditLog]) -> None:
        self.telegram = telegram
        self.audit_log = audit_log

    def health(self, telegram_id: int) -> None:
        """Проверяет доступность Telegram API через текущий клиент."""

        self.telegram.healthcheck()
        self.telegram.send_message(telegram_id, BotInfo.TELEGRAM_API_OK)

    def about(self, telegram_id: int) -> None:
        """Показывает справочную информацию о боте."""

        self.telegram.send_message(telegram_id, BotInfo.ABOUT)

    def whoami(self, telegram_id: int | None, username: str | None) -> None:
        """Возвращает публичную информацию о Telegram-пользователе."""

        if telegram_id is None:
            return
        self.telegram.send_message(telegram_id, format_whoami(telegram_id, username), reply_markup=build_guest_menu())

    def last_action(self, telegram_id: int) -> None:
        """Показывает последнюю запись в журнале команд."""

        actions = self.audit_log.list_recent(1)
        if not actions:
            self.telegram.send_message(telegram_id, AuditLogMessagesV2.Status.IS_EMPTY)
            return

        self.telegram.send_message(telegram_id, format_last_action(actions[0]))

    def status(self, telegram_id: int) -> None:
        """Показывает сводный статус готовности профиля и интеграций."""

        status = SystemStatusService.get_status(telegram_id)

        def icon(value: bool) -> str:
            return "✅" if value else "❌"

        message = (
            "📊 Статус системы\n\n"
            "Профиль:\n"
            f"{icon(status.company)} Компания\n"
            f"{icon(status.bank_details)} Банковские реквизиты\n"
            f"{icon(status.signature)} Подпись\n\n"
            "Интеграции:\n"
            f"{icon(status.gmail)} Gmail\n\n"
            "Документы:\n"
            f"{icon(status.bank_confirmation_available)} Bank Confirmation\n"
            f"{icon(status.invoice_available)} Salary Invoice\n"
            f"{icon(status.conversion_order_available)} Conversion Order"
        )

        self.telegram.send_message(telegram_id, message)
