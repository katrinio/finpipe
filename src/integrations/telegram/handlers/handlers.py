from collections.abc import Callable
from dataclasses import dataclass

from src.constants import Dir
from src.integrations.gmail.account_service import GmailAccountService
from src.integrations.gmail.gmail_oauth import GmailOAuth
from src.integrations.gmail.settings import GmailOAuthSettings
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import BotInfo, Cmd, build_help_message, format_last_action, format_whoami
from src.integrations.telegram.handlers.menu_handlers import MenuHandler
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.buttons import (
    GmailButtons,
    MainMenuButtons,
    NavigationButtons,
    SettingsButtons,
    SignatureButtons,
    SystemButtons,
)
from src.services.profile_template.exceptions import InvalidProfileTemplateError, InvalidProfileTemplateFormatError, ProfileTemplateTooLargeError
from src.services.profile_template.profile_template_service import ProfileTemplateService
from src.services.signing.exceptions import InvalidSignatureFormatError, InvalidSignatureImageError, SignatureTooLargeError
from src.services.signing.signature_service import SignatureService
from src.storage.orm import Signature
from src.storage.orm.system.audit_log import AuditLog, AuditStatus
from src.utils.credentials import LOGGER, EnvVar
from src.workflows.run_invoice_delivery import generate_and_send_invoice


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
        self.menu_handler = MenuHandler(self.telegram)
        # TODO(LOW):
        # Список команд уже заметно вырос и смешивает навигацию, сервисные действия и upload-flow.
        # После стабилизации интерфейса нужно разнести команды и UI-кнопки по отдельным модулям.
        self.state_service = UserStateService()
        self._command_handlers: dict[str, Callable[[CommandContext], None]] = {}
        self._build_command_handlers()

    def handle_message(self, text: str, telegram_id: int | None, username: str | None) -> bool:
        """Выполняет команду Telegram."""
        if telegram_id is None:
            return False

        context = CommandContext(
            telegram_id=telegram_id,
            username=username,
            command=text,
        )

        try:
            handler = self._command_handlers.get(text)

            if handler is None:
                self.telegram.send_message(BotInfo.NO_SUCH_COMMAND)
                self._audit(context, AuditStatus.FAILED, BotInfo.NO_SUCH_COMMAND)
            else:
                handler(context)
                self._audit(context, AuditStatus.SUCCESS)

        except Exception as error:
            LOGGER.exception("Command failed: %s", text)
            self.telegram.send_message(f"{BotInfo.SYSTEM_ERROR}\nCommand {text} failed:\n{error}")
            self._audit(context, AuditStatus.FAILED, str(error))

            return False

        return True

    def _build_command_handlers(self) -> None:
        """Собирает таблицу команд один раз при инициализации."""

        self._command_handlers = {
            Cmd.INVOICE: lambda context: self._invoice(),
            Cmd.MENU: lambda context: self.menu_handler.main_menu(),
            MainMenuButtons.GMAIL: lambda context: self.menu_handler.gmail_menu(),
            MainMenuButtons.SYSTEM: lambda context: self.menu_handler.system_menu(),
            MainMenuButtons.SIGNATURE: lambda context: self.menu_handler.signature_menu(),
            MainMenuButtons.SETTINGS: lambda context: self.menu_handler.settings_menu(),
            GmailButtons.GMAIL_CONNECT: lambda context: self._gmail_connect(context.telegram_id, context.username),
            GmailButtons.GMAIL_DISCONNECT: lambda context: self._gmail_disconnect(context.telegram_id),
            GmailButtons.GMAIL_STATUS: lambda context: self._gmail_status(context.telegram_id),
            SignatureButtons.SIGNATURE_DELETE: lambda context: self._delete_signature(context.telegram_id),
            SignatureButtons.SIGNATURE_STATUS: lambda context: self._signature_status(context.telegram_id),
            SignatureButtons.SIGNATURE_UPLOAD: lambda context: self._upload_signature(context.telegram_id),
            SystemButtons.ABOUT: lambda context: self._about(),
            SystemButtons.HEALTHCHECK: lambda context: self._health(),
            SystemButtons.HELP: lambda context: self._help(),
            SystemButtons.LAST_ACTION: lambda context: self._last_action(),
            SystemButtons.SYSTEM_STATUS: lambda context: self._status(),
            SystemButtons.WHOAMI: lambda context: self._whoami(context.telegram_id, context.username),
            SettingsButtons.DOWNLOAD_TEMPLATE: lambda context: self._download_template(context.telegram_id),
            SettingsButtons.UPLOAD_TEMPLATE: lambda context: self._upload_template(context.telegram_id),
            NavigationButtons.BACK: lambda context: self.menu_handler.main_menu(),
        }

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
        try:
            generate_and_send_invoice()
        except ValueError as error:
            self.telegram.send_message(str(error))
            return
        self.telegram.send_message(BotInfo.INVOICE_SENT)

    def _about(self) -> None:
        self.telegram.send_message(BotInfo.ABOUT)

    def _whoami(self, telegram_id: int | None, username: str | None) -> None:
        self.telegram.send_message(format_whoami(telegram_id, username))

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
        self.telegram.send_message(BotInfo.GMAIL_DISCONNECTED)

    def _upload_signature(self, telegram_id: int) -> None:
        self.state_service.set_state(telegram_id, UserState.WAITING_SIGNATURE_UPLOAD)
        self.telegram.send_message(BotInfo.SIGNATURE_REQUIREMENTS)

    def _handle_signature_upload(self, telegram_id: int, file_name: str, file_size: int, file_bytes: bytes) -> None:
        try:
            SignatureService.upload(
                telegram_id=telegram_id,
                file_name=file_name,
                file_size=file_size,
                file_bytes=file_bytes,
            )
        except InvalidSignatureFormatError:
            self.telegram.send_message(BotInfo.SIGNATURE_NOT_PNG)
            return
        except SignatureTooLargeError:
            self.telegram.send_message(BotInfo.SIGNATURE_TOO_LARGE)
            return
        except InvalidSignatureImageError:
            self.telegram.send_message(BotInfo.SIGNATURE_UPLOAD_ERROR)
            return

        self.state_service.clear_state(telegram_id)
        self.telegram.send_message(BotInfo.SIGNATURE_UPDATED)

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

    def _handle_profile_template_upload(self, telegram_id: int, file_name: str, file_size: int, file_bytes: bytes) -> None:
        try:
            ProfileTemplateService.upload(
                telegram_id=telegram_id,
                file_name=file_name,
                file_size=file_size,
                file_bytes=file_bytes,
            )
        except InvalidProfileTemplateFormatError:
            self.telegram.send_message(BotInfo.PROFILE_TEMPLATE_NOT_YAML)
            return
        except ProfileTemplateTooLargeError:
            self.telegram.send_message(BotInfo.PROFILE_TEMPLATE_TOO_LARGE)
            return
        except InvalidProfileTemplateError:
            self.telegram.send_message(BotInfo.PROFILE_TEMPLATE_UPLOAD_ERROR)
            return

        self.state_service.clear_state(telegram_id)
        self.telegram.send_message(BotInfo.PROFILE_TEMPLATE_UPDATED)

    def _upload_template(self, telegram_id: int) -> None:
        self.state_service.set_state(telegram_id, UserState.WAITING_PROFILE_TEMPLATE_UPLOAD)
        self.telegram.send_message(BotInfo.PROFILE_TEMPLATE_SENT)

    def _download_template(self, telegram_id: int) -> None:
        self.telegram.send_document(document_path=Dir.PROFILE_TEMPLATE)
        self.telegram.send_message(BotInfo.PROFILE_TEMPLATE_SENT)
