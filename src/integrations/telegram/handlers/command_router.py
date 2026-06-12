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
    InvoiceMenuButtons,
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
            if handler is None and text.startswith(f"{Cmd.ADD_USER} "):
                handler = self._command_handlers.get(OwnerButtons.ADD_USER)
            if handler is None and text.startswith(f"{Cmd.REMOVE_USER} "):
                handler = self._command_handlers.get(OwnerButtons.REMOVE_USER)
            if handler is None and text.startswith(f"{OwnerButtons.ADD_USER} "):
                handler = self._command_handlers.get(OwnerButtons.ADD_USER)
            if handler is None and text.startswith(f"{OwnerButtons.REMOVE_USER} "):
                handler = self._command_handlers.get(OwnerButtons.REMOVE_USER)

            if handler is None:
                self.telegram.send_message(context.telegram_id, BotInfo.NO_SUCH_COMMAND)
                self._audit(context, AuditStatus.FAILED, BotInfo.NO_SUCH_COMMAND)
            else:
                handler(context)
                self._audit(context, AuditStatus.SUCCESS)

        except Exception as error:
            LOGGER.exception("Command failed: %s", text)
            self.telegram.send_message(context.telegram_id, f"{BotInfo.SYSTEM_ERROR}\nCommand {text} failed:\n{error}")
            self._audit(context, AuditStatus.FAILED, str(error))

            return False

        return True

    def _build_command_handlers(self) -> None:
        """Собирает таблицу команд один раз при инициализации."""

        self._command_handlers = {
            # root navigation
            Cmd.START: lambda context: self.menu_handler.main_start(context.telegram_id),
            Cmd.MENU: lambda context: self.menu_handler.main_menu(context.telegram_id),
            # main menu
            MainMenuButtons.DOCUMENTS: lambda context: self.menu_handler.document_menu(context.telegram_id),
            MainMenuButtons.INTEGRATIONS: lambda context: self.menu_handler.integration_menu(context.telegram_id),
            MainMenuButtons.PROFILE: lambda context: self.menu_handler.settings_menu(context.telegram_id),
            MainMenuButtons.SYSTEM: lambda context: self.menu_handler.system_menu(context.telegram_id),
            OwnerButtons.ADMIN_PANEL: lambda context: self.menu_handler.admin_menu(context.telegram_id),
            NavigationButtons.BACK: lambda context: self.menu_handler.main_menu(context.telegram_id),
            # documents
            DocumentsMenuButtons.SALARY_INVOICE: lambda context: self.menu_handler.invoice_menu(context.telegram_id),
            DocumentsMenuButtons.BANK_CONFIRMATION: lambda context: self.document_handler.bank_confirmation(context.telegram_id),
            DocumentsMenuButtons.CONVERSION_ORDER: lambda context: self.document_handler.conversion_order(context.telegram_id),
            # invoice
            InvoiceMenuButtons.SET_INVOICE_AMOUNT: lambda context: self.document_handler.start_invoice_amount_input(context.telegram_id),
            InvoiceMenuButtons.GET_INVOICE_AMOUNT: lambda context: self.document_handler.get_invoice_amount(context.telegram_id),
            InvoiceMenuButtons.GENERATE_INVOICE: lambda context: self.document_handler.invoice(context.telegram_id),
            # profile
            ProfileButtons.DOWNLOAD_TEMPLATE: lambda context: self.profile_handler.download_template(context.telegram_id),
            ProfileButtons.UPLOAD_TEMPLATE: lambda context: self.profile_handler.upload_template(context.telegram_id),
            ProfileButtons.MY_PROFILE: lambda context: self.profile_handler.show_profile(context.telegram_id),
            # signature
            SystemButtons.STATUS: lambda context: self.system_handler.status(context.telegram_id),
            SignatureButtons.SIGNATURE_UPLOAD: lambda context: self.signature_handler.upload_signature(context.telegram_id),
            SignatureButtons.SIGNATURE_DELETE: lambda context: self.signature_handler.delete_signature(context.telegram_id),
            SignatureButtons.SIGNATURE_STATUS: lambda context: self.signature_handler.signature_status(context.telegram_id),
            # integrations
            IntegrationsButtons.GMAIL: lambda context: self.menu_handler.gmail_menu(context.telegram_id),
            # gmail
            GmailButtons.GMAIL_CONNECT: lambda context: self.gmail_handler.gmail_connect(context.telegram_id, context.username),
            GmailButtons.GMAIL_DISCONNECT: lambda context: self.gmail_handler.gmail_disconnect(context.telegram_id),
            GmailButtons.GMAIL_STATUS: lambda context: self.gmail_handler.gmail_status(context.telegram_id),
            # system
            SystemButtons.ABOUT: lambda context: self.system_handler.about(context.telegram_id),
            SystemButtons.HEALTHCHECK: lambda context: self.system_handler.health(context.telegram_id),
            SystemButtons.HELP: lambda context: self._help(context.telegram_id),
            SystemButtons.WHOAMI: lambda context: self.system_handler.whoami(context.telegram_id, context.username),
            # admin
            OwnerButtons.USERS: lambda context: self.menu_handler.user_menu(context.telegram_id),
            OwnerButtons.ADD_USER: lambda context: (
                self.owner_handler.start_add_user_input(context.telegram_id)
                if context.command == OwnerButtons.ADD_USER
                else self.owner_handler.add_user(context.telegram_id, context.command)
            ),
            OwnerButtons.REMOVE_USER: lambda context: (
                self.owner_handler.start_remove_user_input(context.telegram_id)
                if context.command == OwnerButtons.REMOVE_USER
                else self.owner_handler.remove_user(context.telegram_id, context.command)
            ),
            OwnerButtons.LIST_USERS: lambda context: self.owner_handler.list_users(context.telegram_id),
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

    def _help(self, telegram_id: int) -> None:
        self.telegram.send_message(telegram_id, build_help_message())


TelegramHandlers = CommandRouter
