from collections.abc import Callable

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import BotInfo, Cmd, build_help_message, format_last_action, format_whoami
from src.storage.repositories.audit_log_repository import AuditLogRepository
from src.utils.credentials import LOGGER
from src.workflows.generate_invoice_and_send import generate_and_send_invoice


class TelegramHandlers:
    """Telegram handlers и действия бота."""

    def __init__(self, telegram: TelegramClient, audit_log: AuditLogRepository):
        self.telegram = telegram
        self.audit_log = audit_log

    def handle_message(self, text: str, telegram_id: int | None, username: str | None) -> bool:
        """Выполняет команду Telegram."""

        handlers: dict[str, Callable[[], None]] = {
            Cmd.STATUS: self._status,
            Cmd.HELP: self._help,
            Cmd.HEALTH: self._health,
            Cmd.INVOICE: self._invoice,
            Cmd.ABOUT: self._about,
            Cmd.WHOAMI: lambda: self._whoami(telegram_id, username),
            Cmd.LAST_ACTION: self._last_action,
        }

        try:
            handler = handlers.get(text)

            if handler is None:
                self.telegram.send_message(BotInfo.NO_SUCH_COMMAND)
            else:
                handler()

        except Exception as error:
            LOGGER.exception("Command failed: %s", text)
            self.telegram.send_message(f"❌ Command {text} failed:\n{error}")

            return False

        return True

    def _status(self) -> None:
        self.telegram.send_message(BotInfo.PROJECT_RUNNING)

    def _help(self) -> None:
        self.telegram.send_message(build_help_message())

    def _health(self) -> None:
        self.telegram.healthcheck()
        self.telegram.send_message(BotInfo.TG_API_OK)

    def _invoice(self) -> None:
        self.telegram.send_message(BotInfo.GENERATING_INVOICE)
        generate_and_send_invoice()
        self.telegram.send_message(BotInfo.INVOICE_SENT)

    def _about(self) -> None:
        self.telegram.send_message(BotInfo.ABOUT)

    def _whoami(self, telegram_id: int | None, username: str | None) -> None:
        self.telegram.send_message(f"{BotInfo.WHOAMI_PREFIX}\n{format_whoami(telegram_id, username)}")

    def _last_action(self) -> None:
        actions = self.audit_log.list_recent(1)
        if not actions:
            self.telegram.send_message(BotInfo.NO_AUDIT_LOG_RECORDS)
            return

        self.telegram.send_message(format_last_action(actions[0]))
