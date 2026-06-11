from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import format_last_action, format_whoami
from src.integrations.telegram.ui.menu.guest_menu import build_guest_menu
from src.integrations.telegram.ui.messages import BotInfo
from src.services.system_status.system_status_service import SystemStatusService
from src.storage.orm.system.audit_log import AuditLog


class SystemHandlers:
    def __init__(self, telegram: TelegramClient, audit_log: type[AuditLog]) -> None:
        self.telegram = telegram
        self.audit_log = audit_log

    def health(self, telegram_id: int) -> None:
        self.telegram.healthcheck()
        self.telegram.send_message(telegram_id, BotInfo.TELEGRAM_API_OK)

    def about(self, telegram_id: int) -> None:
        self.telegram.send_message(telegram_id, BotInfo.ABOUT)

    def whoami(self, telegram_id: int | None, username: str | None) -> None:
        if telegram_id is None:
            return
        self.telegram.send_message(telegram_id, format_whoami(telegram_id, username), reply_markup=build_guest_menu())

    def last_action(self, telegram_id: int) -> None:
        actions = self.audit_log.list_recent(1)
        if not actions:
            self.telegram.send_message(telegram_id, BotInfo.NO_AUDIT_LOG_RECORDS)
            return

        self.telegram.send_message(telegram_id, format_last_action(actions[0]))

    def status(self, telegram_id: int) -> None:
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
            f"{icon(status.bank_pdf_available)} Bank PDF\n"
            f"{icon(status.invoice_available)} Invoice\n"
            f"{icon(status.transfer_request_available)} Transfer Request"
        )

        self.telegram.send_message(telegram_id, message)
