from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import format_last_action, format_whoami
from src.integrations.telegram.ui.messages import BotInfo
from src.storage.orm.system.audit_log import AuditLog


class SystemHandlers:
    def __init__(self, telegram: TelegramClient, audit_log: type[AuditLog]) -> None:
        self.telegram = telegram
        self.audit_log = audit_log

    def status(self) -> None:
        self.telegram.send_message(BotInfo.PROJECT_RUNNING)

    def health(self) -> None:
        self.telegram.healthcheck()
        self.telegram.send_message(BotInfo.TELEGRAM_API_OK)

    def about(self) -> None:
        self.telegram.send_message(BotInfo.ABOUT)

    def whoami(self, telegram_id: int | None, username: str | None) -> None:
        self.telegram.send_message(format_whoami(telegram_id, username))

    def last_action(self) -> None:
        actions = self.audit_log.list_recent(1)
        if not actions:
            self.telegram.send_message(BotInfo.NO_AUDIT_LOG_RECORDS)
            return

        self.telegram.send_message(format_last_action(actions[0]))
