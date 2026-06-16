from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import format_last_action, format_recent_errors, format_stats, format_whoami
from src.integrations.telegram.messages import AuditLogMessages, CommonMessages
from src.integrations.telegram.ui.menu.admin_menu import build_admin_menu
from src.integrations.telegram.ui.menu.guest_menu import build_guest_menu
from src.integrations.telegram.ui.menu.system_menu import build_system_menu
from src.services.monitoring.event_analytics import EventAnalytics
from src.services.system_status.system_status_service import SystemStatusService
from src.storage.orm import AllowedUser
from src.storage.orm.system.audit_log import AuditLog


class SystemHandlers:
    """Обрабатывает системные команды Telegram-бота."""

    def __init__(self, telegram: TelegramClient, audit_log: type[AuditLog]) -> None:
        self.telegram = telegram
        self.audit_log = audit_log

    def health(self, telegram_id: int) -> None:
        """Проверяет доступность Telegram API через текущий клиент."""

        self.telegram.healthcheck()
        self.telegram.send_message(
            telegram_id,
            CommonMessages.Status.TELEGRAM_API_OK,
            reply_markup=build_system_menu(is_owner=AllowedUser.is_owner(telegram_id)),
        )

    def about(self, telegram_id: int) -> None:
        """Показывает справочную информацию о боте."""

        self.telegram.send_message(
            telegram_id,
            CommonMessages.General.ABOUT,
            reply_markup=build_system_menu(is_owner=AllowedUser.is_owner(telegram_id)),
        )

    def whoami(self, telegram_id: int | None, username: str | None) -> None:
        """Возвращает публичную информацию о Telegram-пользователе."""

        if telegram_id is None:
            return
        reply_markup = build_system_menu(is_owner=AllowedUser.is_owner(telegram_id)) if AllowedUser.exists(telegram_id) else build_guest_menu()
        self.telegram.send_message(telegram_id, format_whoami(telegram_id, username), reply_markup=reply_markup)

    def last_action(self, telegram_id: int) -> None:
        """Показывает последнюю запись в журнале команд."""

        actions = self.audit_log.list_recent(1)
        if not actions:
            self.telegram.send_message(
                telegram_id,
                AuditLogMessages.Status.IS_EMPTY,
                reply_markup=build_system_menu(is_owner=AllowedUser.is_owner(telegram_id)),
            )
            return

        self.telegram.send_message(
            telegram_id,
            format_last_action(actions[0]),
            reply_markup=build_system_menu(is_owner=AllowedUser.is_owner(telegram_id)),
        )

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

        self.telegram.send_message(telegram_id, message, reply_markup=build_system_menu(is_owner=AllowedUser.is_owner(telegram_id)))

    def statistics(self, telegram_id: int) -> None:
        """Показывает компактную аналитику по продуктовым событиям."""

        analytics = EventAnalytics()
        self.telegram.send_message(
            telegram_id,
            format_stats(
                total_events=analytics.get_total_events(),
                event_counts=analytics.get_event_counts(),
                document_stats=analytics.get_document_generation_stats(),
                error_count=analytics.get_error_counts(),
                recent_error_count=len(analytics.get_recent_errors(limit=3)),
            ),
            reply_markup=build_admin_menu(),
        )

    def recent_errors(self, telegram_id: int) -> None:
        """Показывает краткую сводку последних ошибок."""

        analytics = EventAnalytics()
        self.telegram.send_message(
            telegram_id,
            format_recent_errors(analytics.get_recent_errors(limit=10)),
            reply_markup=build_admin_menu(),
        )
