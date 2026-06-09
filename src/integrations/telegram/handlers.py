from collections.abc import Callable
from dataclasses import dataclass

from src.integrations.gmail.account_service import GmailAccountService
from src.integrations.gmail.gmail_oauth import GmailOAuth
from src.integrations.gmail.settings import GmailOAuthSettings
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import BotInfo, Cmd, build_help_message, format_last_action, format_whoami
from src.storage.orm.audit_log import AuditStatus
from src.storage.repositories.audit_log_repository import AuditLogRepository
from src.utils.credentials import LOGGER, EnvVar
from src.workflows.generate_invoice_and_send import generate_and_send_invoice


@dataclass(frozen=True)
class CommandContext:
    """Контекст Telegram-команды для аудита."""

    telegram_id: int
    username: str | None
    command: str


class TelegramHandlers:
    """Telegram handlers и действия бота."""

    def __init__(self, telegram: TelegramClient, audit_log: AuditLogRepository):
        self.telegram = telegram
        self.audit_log = audit_log

    def handle_message(self, text: str, telegram_id: int | None, username: str | None) -> bool:
        """Выполняет команду Telegram."""

        if telegram_id is None:
            return False

        context = CommandContext(
            telegram_id=telegram_id,
            username=username,
            command=text,
        )

        handlers: dict[str, Callable[[], None]] = {
            Cmd.STATUS: self._status,
            Cmd.HELP: self._help,
            Cmd.HEALTH: self._health,
            Cmd.INVOICE: self._invoice,
            Cmd.ABOUT: self._about,
            Cmd.WHOAMI: lambda: self._whoami(context.telegram_id, context.username),
            Cmd.LAST_ACTION: self._last_action,
            Cmd.CONNECT_GMAIL: lambda: self._gmail_connect(context.telegram_id, context.username),
            Cmd.GMAIL_STATUS: lambda: self._gmail_status(context.telegram_id),
            Cmd.DISCONNECT_GMAIL: lambda: self._gmail_disconnect(context.telegram_id),
        }

        try:
            handler = handlers.get(text)

            if handler is None:
                self.telegram.send_message(BotInfo.NO_SUCH_COMMAND)
                self._audit(context, AuditStatus.FAILED, "Unknown command")
            else:
                handler()
                self._audit(context, AuditStatus.SUCCESS)

        except Exception as error:
            LOGGER.exception("Command failed: %s", text)
            self.telegram.send_message(f"❌ Command {text} failed:\n{error}")
            self._audit(context, AuditStatus.FAILED, str(error))

            return False

        return True

    def _audit(
        self,
        context: CommandContext,
        status: AuditStatus,
        details: str = "",
    ) -> None:
        """Сохраняет запись аудита команды."""

        self.audit_log.add(
            context.telegram_id,
            context.username or "",
            context.command,
            status,
            details or None,
        )

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

    def _gmail_connect(self, telegram_id: int, username: str | None) -> None:
        if not GmailOAuthSettings.is_callback_enabled():
            self.telegram.send_message(BotInfo.GMAIL_OAUTH_TEMPORARILY_UNAVAILABLE)
            return
        callback_url = EnvVar.get_optional_env("GMAIL_OAUTH_CALLBACK_URL", "http://localhost:8000/oauth/gmail/callback")
        authorization_url, _session = GmailOAuth.build_authorization_url(telegram_id, username, callback_url)
        self.telegram.send_message(f"Open this URL:\n{authorization_url}")

    def _gmail_status(self, telegram_id: int) -> None:
        status = GmailAccountService.status(telegram_id)
        if not status.is_connected:
            self.telegram.send_message(BotInfo.GMAIL_NOT_CONNECTED)
            return
        self.telegram.send_message(f"{BotInfo.GMAIL_CONNECTED}\n{status.gmail_email or 'unknown'}")

    def _gmail_disconnect(self, telegram_id: int) -> None:
        GmailAccountService.disconnect(telegram_id)
        self.telegram.send_message("✅ Gmail disconnected")
