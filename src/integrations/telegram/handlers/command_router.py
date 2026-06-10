from collections.abc import Callable
from dataclasses import dataclass

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import BotInfo, Cmd, build_help_message
from src.integrations.telegram.handlers.document_handlers import DocumentHandlers
from src.integrations.telegram.handlers.gmail_handlers import GmailHandlers
from src.integrations.telegram.handlers.menu_handlers import MenuHandler
from src.integrations.telegram.handlers.owner_handler import OwnerHandlers
from src.integrations.telegram.handlers.profile_handlers import ProfileHandlers
from src.integrations.telegram.handlers.signature_handlers import SignatureHandlers
from src.integrations.telegram.handlers.system_handlers import SystemHandlers
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.ui.buttons import (
    DocumentsMenuButtons,
    GmailButtons,
    IntegrationsButtons,
    MainMenuButtons,
    NavigationButtons,
    OwnerButtons,
    ProfileButtons,
    SignatureButtons,
    SystemButtons,
)
from src.services.signing.signature_service import SignatureService as _SignatureService
from src.storage.orm.system.audit_log import AuditLog, AuditStatus
from src.utils.credentials import LOGGER

SignatureService = _SignatureService


@dataclass(frozen=True)
class CommandContext:
    """Контекст Telegram-команды для аудита."""

    telegram_id: int
    username: str | None
    command: str


class CommandRouter:
    """Маршрутизатор Telegram-команд."""

    def __init__(self, telegram: TelegramClient, audit_log: type[AuditLog]):
        self.telegram = telegram
        self.state_service = UserStateService()
        self.menu_handler = MenuHandler(self.telegram)
        self.system_handler = SystemHandlers(self.telegram, audit_log)
        self.gmail_handler = GmailHandlers(self.telegram)
        self.document_handler = DocumentHandlers(self.telegram)
        self.owner_handler = OwnerHandlers(self.telegram)
        self.signature_handler = SignatureHandlers(self.telegram, self.state_service)
        self.profile_handler = ProfileHandlers(self.telegram, self.state_service)
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
            OwnerButtons.ADD_USER: lambda context: self.owner_handler.add_user(
                telegram_id=context.telegram_id,
                command=context.command,
                username=context.username,
            ),
            Cmd.MENU: lambda context: self.menu_handler.main_menu(),
            MainMenuButtons.DOCUMENTS: lambda context: self.menu_handler.document_menu(),
            MainMenuButtons.INTEGRATIONS: lambda context: self.menu_handler.integration_menu(),
            MainMenuButtons.PROFILE: lambda context: self.menu_handler.settings_menu(),
            MainMenuButtons.SYSTEM: lambda context: self.menu_handler.system_menu(),
            NavigationButtons.BACK: lambda context: self.menu_handler.main_menu(),
            DocumentsMenuButtons.INVOICE: lambda context: self.document_handler.invoice(),
            DocumentsMenuButtons.BANK: lambda context: self.document_handler.bank(),
            DocumentsMenuButtons.TRANSFER_REQUEST: lambda context: self.document_handler.transfer_request(),
            ProfileButtons.DOWNLOAD_TEMPLATE: lambda context: self.profile_handler.download_template(context.telegram_id),
            ProfileButtons.UPLOAD_TEMPLATE: lambda context: self.profile_handler.upload_template(context.telegram_id),
            SystemButtons.STATUS: lambda context: self.system_handler.status(context.telegram_id),
            SignatureButtons.SIGNATURE_UPLOAD: lambda context: self.signature_handler.upload_signature(context.telegram_id),
            SignatureButtons.SIGNATURE_DELETE: lambda context: self.signature_handler.delete_signature(context.telegram_id),
            SignatureButtons.SIGNATURE_STATUS: lambda context: self.signature_handler.signature_status(context.telegram_id),
            IntegrationsButtons.GMAIL: lambda context: self.menu_handler.gmail_menu(),
            GmailButtons.GMAIL_CONNECT: lambda context: self.gmail_handler.gmail_connect(context.telegram_id, context.username),
            GmailButtons.GMAIL_DISCONNECT: lambda context: self.gmail_handler.gmail_disconnect(context.telegram_id),
            GmailButtons.GMAIL_STATUS: lambda context: self.gmail_handler.gmail_status(context.telegram_id),
            SystemButtons.ABOUT: lambda context: self.system_handler.about(),
            SystemButtons.HEALTHCHECK: lambda context: self.system_handler.health(),
            SystemButtons.HELP: lambda context: self._help(),
            SystemButtons.WHOAMI: lambda context: self.system_handler.whoami(context.telegram_id, context.username),
        }

    def _audit(
        self,
        context: CommandContext,
        status: AuditStatus,
        details: str = "",
    ) -> None:
        """Сохраняет запись аудита команды."""

        self.system_handler.audit_log.create(
            context.telegram_id,
            context.username or "",
            context.command,
            status,
            details or None,
        )

    def _help(self) -> None:
        self.telegram.send_message(build_help_message())


TelegramHandlers = CommandRouter
