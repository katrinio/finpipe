from collections.abc import Callable
from dataclasses import dataclass

from src.integrations.gmail.account_service import GmailAccountService
from src.integrations.gmail.gmail_oauth import GmailOAuth
from src.integrations.gmail.settings import GmailOAuthSettings
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import BotInfo, Cmd, build_help_message, format_last_action, format_whoami
from src.integrations.telegram.states import UserState
from src.services.signing.exceptions import InvalidSignatureFormatError, InvalidSignatureImageError, SignatureTooLargeError
from src.services.signing.signature_service import SignatureService
from src.storage.orm import Signature
from src.storage.orm.audit_log import AuditLog, AuditStatus
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

    def __init__(self, telegram: TelegramClient, audit_log: type[AuditLog]):
        self.telegram = telegram
        self.audit_log = audit_log
        # TODO:
        # User states are stored in memory only.
        # After process restart all active flows are lost.
        # Persist states in DB if interactive Telegram workflows grow.
        self._user_states: dict[int, UserState] = {}

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
            Cmd.UPLOAD_SIGNATURE: lambda: self._upload_signature(context.telegram_id),
            Cmd.DELETE_SIGNATURE: lambda: self._delete_signature(context.telegram_id),
            Cmd.SIGNATURE_STATUS: lambda: self._signature_status(context.telegram_id),
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

        self.audit_log.create(
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
        self.telegram.send_message(BotInfo.TELEGRAM_API_OK)

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
        return

    def _gmail_connect(self, telegram_id: int, username: str | None) -> None:
        if not GmailOAuthSettings.is_callback_enabled():
            self.telegram.send_message(BotInfo.GMAIL_OAUTH_TEMPORARILY_UNAVAILABLE)
            return
        callback_url = EnvVar.get_optional_env("GMAIL_OAUTH_CALLBACK_URL", "http://localhost:8000/oauth/gmail/callback")
        authorization_url, _session = GmailOAuth.build_authorization_url(telegram_id, username, callback_url)
        self.telegram.send_message(f"Open this URL:\n{authorization_url}")
        return

    def _gmail_status(self, telegram_id: int) -> None:
        status = GmailAccountService.status(telegram_id)
        if not status.is_connected:
            self.telegram.send_message(BotInfo.GMAIL_NOT_CONNECTED)
            return
        self.telegram.send_message(f"{BotInfo.GMAIL_CONNECTED}\n{status.gmail_email or 'unknown'}")

    def _gmail_disconnect(self, telegram_id: int) -> None:
        GmailAccountService.disconnect(telegram_id)
        self.telegram.send_message("✅ Gmail disconnected")

    def _upload_signature(self, telegram_id: int) -> None:
        self.set_user_state(telegram_id, UserState.WAITING_SIGNATURE_UPLOAD)
        self.telegram.send_message("✍️ Пришлите подпись в PNG формате.\nТребования:\n- PNG\n- до 2 МБ\n- прозрачный фон рекомендуется")

    def _handle_signature_upload(self, telegram_id: int, file_name: str, file_size: int, file_bytes: bytes) -> None:
        try:
            SignatureService.upload(
                telegram_id=telegram_id,
                file_name=file_name,
                file_size=file_size,
                file_bytes=file_bytes,
            )
        except InvalidSignatureFormatError:
            self.telegram.send_message("❌ Разрешены только PNG файлы")
            return
        except SignatureTooLargeError:
            self.telegram.send_message("❌ Размер файла превышает 2 МБ")
            return
        except InvalidSignatureImageError:
            self.telegram.send_message("❌ Не удалось обработать изображение")
            return

        self.clear_user_state(telegram_id)
        self.telegram.send_message("✅ Подпись успешно обновлена")

    def _delete_signature(self, telegram_id: int) -> None:
        signature = Signature.get_active(telegram_id)
        if signature is None:
            self.telegram.send_message(BotInfo.SIGNATURE_NOT_FOUND)
            return

        Signature.delete(telegram_id)
        self.telegram.send_message(BotInfo.SIGNATURE_DELETED)

    def _signature_status(self, telegram_id: int) -> None:
        if not Signature.exists(telegram_id):
            self.telegram.send_message(BotInfo.SIGNATURE_NOT_FOUND)
            return

        self.telegram.send_message(BotInfo.SIGNATURE_FOUND)
        return

    def set_user_state(self, telegram_id: int, state: UserState) -> None:
        """Сохраняет простое состояние пользователя в памяти."""

        self._user_states[telegram_id] = state

    def get_user_state(self, telegram_id: int) -> UserState | None:
        """Возвращает текущее состояние пользователя."""

        return self._user_states.get(telegram_id)

    def clear_user_state(self, telegram_id: int) -> None:
        """Сбрасывает состояние пользователя."""

        self._user_states.pop(telegram_id, None)
