from collections.abc import Callable
from dataclasses import dataclass

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import Cmd
from src.integrations.telegram.handlers.document_handlers import DocumentHandlers
from src.integrations.telegram.handlers.gmail_handlers import GmailHandlers
from src.integrations.telegram.handlers.menu_handlers import MenuHandler
from src.integrations.telegram.handlers.monitoring_handler import MonitoringHandler
from src.integrations.telegram.handlers.owner_handler import OwnerHandlers
from src.integrations.telegram.handlers.profile_handlers import ProfileHandlers
from src.integrations.telegram.handlers.signature_handlers import SignatureHandlers
from src.integrations.telegram.handlers.system_handlers import SystemHandlers
from src.integrations.telegram.messages.menu_messages import MenuMessages
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.ui.buttons import (
    BankDayButtons,
    DocumentsMenuButtons,
    GmailButtons,
    InvoiceMenuButtons,
    MainMenuButtons,
    NavigationButtons,
    OwnerButtons,
    ProfileButtons,
    SignatureButtons,
    SystemButtons,
)
from src.integrations.telegram.ui.messages import CommonMessages
from src.services.monitoring.event_logger import EventLogger
from src.services.signing.signature_service import SignatureService as _SignatureService
from src.storage.orm import AllowedUser
from src.storage.orm.system.app_events import EventSeverity, EventType
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
        self.monitoring_handler = MonitoringHandler(self.telegram)
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
            if text == SystemButtons.CHATID and not AllowedUser.is_owner(context.telegram_id):
                self.telegram.send_message(context.telegram_id, CommonMessages.Errors.NO_SUCH_COMMAND)
                self._audit(context, AuditStatus.FAILED, CommonMessages.Errors.NO_SUCH_COMMAND)
                return False

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
                self.telegram.send_message(context.telegram_id, CommonMessages.Errors.NO_SUCH_COMMAND)
                self._audit(context, AuditStatus.FAILED, CommonMessages.Errors.NO_SUCH_COMMAND)
            else:
                handler(context)
                self._audit(context, AuditStatus.SUCCESS)

        except Exception as error:
            LOGGER.exception(
                "Command failed for telegram user %s: %s",
                context.telegram_id,
                self._summarize_command(text),
            )
            EventLogger.log(
                EventType.ERROR,
                EventSeverity.ERROR,
                {
                    "telegram_id": context.telegram_id,
                    "category": "telegram",
                    "command": self._summarize_command(text),
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                },
            )
            self.telegram.send_message(context.telegram_id, CommonMessages.Errors.SYSTEM_ERROR)
            self._audit(context, AuditStatus.FAILED, str(error))

            return False

        return True

    def _build_command_handlers(self) -> None:
        """Собирает таблицу команд один раз при инициализации."""

        self._command_handlers = {
            # root navigation
            Cmd.START: lambda context: self.menu_handler.main_start(context.telegram_id),
            Cmd.MENU: lambda context: self.menu_handler.main_menu(context.telegram_id),
            # main menu (inline callback_data)
            MainMenuButtons.CB_DOCUMENTS: lambda context: self.menu_handler.document_menu(context.telegram_id),
            MainMenuButtons.CB_INTEGRATIONS: lambda context: self.menu_handler.gmail_menu(context.telegram_id),
            MainMenuButtons.CB_PROFILE: lambda context: self.menu_handler.settings_menu(context.telegram_id),
            MainMenuButtons.CB_SYSTEM: lambda context: self.menu_handler.system_menu(context.telegram_id),
            MainMenuButtons.CB_ADMIN: lambda context: self.menu_handler.admin_menu(context.telegram_id),
            # legacy text navigation (HOME кнопка в подменю, /menu команда)
            NavigationButtons.HOME: lambda context: self.menu_handler.main_menu(context.telegram_id),
            MenuMessages.MAIN_MENU: lambda context: self.menu_handler.main_menu(context.telegram_id),
            # documents (inline callback_data)
            DocumentsMenuButtons.CB_INVOICE: lambda context: self.menu_handler.invoice_menu(context.telegram_id),
            DocumentsMenuButtons.CB_BANK_DAY_INFO: lambda context: self.document_handler.bank_day_info(context.telegram_id),
            DocumentsMenuButtons.CB_BANK_DAY_START: lambda context: self.document_handler.bank_day(context.telegram_id),
            DocumentsMenuButtons.CB_BACK: lambda context: self.menu_handler.main_menu(context.telegram_id),
            BankDayButtons.CB_REPLY: lambda context: self.document_handler.bank_day_reply_to_bank(context.telegram_id),
            BankDayButtons.CB_SKIP: lambda context: self.document_handler.bank_day_skip_reply(context.telegram_id),
            # invoice (inline callback_data)
            InvoiceMenuButtons.CB_SET_AMOUNT: lambda context: self.document_handler.start_invoice_amount_input(context.telegram_id),
            InvoiceMenuButtons.CB_GET_AMOUNT: lambda context: self.document_handler.get_invoice_amount(context.telegram_id),
            InvoiceMenuButtons.CB_GENERATE: lambda context: self.document_handler.invoice(context.telegram_id),
            InvoiceMenuButtons.CB_BACK: lambda context: self.menu_handler.document_menu(context.telegram_id),
            InvoiceMenuButtons.CB_SEND_TO_COMPANY: lambda context: self.document_handler.invoice_send_to_company(context.telegram_id),
            InvoiceMenuButtons.CB_SKIP_SEND: lambda context: self.document_handler.invoice_skip_send(context.telegram_id),
            # profile (inline callback_data)
            ProfileButtons.CB_VIEW: lambda context: self.profile_handler.show_profile(context.telegram_id),
            ProfileButtons.CB_DOWNLOAD_TEMPLATE: lambda context: self.profile_handler.download_template(context.telegram_id),
            ProfileButtons.CB_UPLOAD_TEMPLATE: lambda context: self.profile_handler.upload_template(context.telegram_id),
            ProfileButtons.CB_BACK: lambda context: self.menu_handler.main_menu(context.telegram_id),
            # signature (inline callback_data)
            SignatureButtons.CB_UPLOAD: lambda context: self.signature_handler.upload_signature(context.telegram_id),
            SignatureButtons.CB_DELETE: lambda context: self.signature_handler.delete_signature(context.telegram_id),
            # gmail (inline callback_data)
            GmailButtons.CB_GMAIL: lambda context: self.menu_handler.gmail_menu(context.telegram_id),
            GmailButtons.CB_CONNECT: lambda context: self.gmail_handler.gmail_connect(context.telegram_id, context.username),
            GmailButtons.CB_DISCONNECT: lambda context: self.gmail_handler.gmail_disconnect(context.telegram_id),
            GmailButtons.CB_STATUS: lambda context: self.gmail_handler.gmail_status(context.telegram_id),
            GmailButtons.CB_CLEAR_HISTORY: lambda context: self.gmail_handler.gmail_clear_history(context.telegram_id),
            GmailButtons.CB_BACK: lambda context: self.menu_handler.main_menu(context.telegram_id),
            # system
            SystemButtons.CB_WHOAMI: lambda context: self.system_handler.whoami(context.telegram_id, context.username),
            SystemButtons.CB_EASY_START: lambda context: self.system_handler.easy_start(context.telegram_id),
            SystemButtons.CB_BACK: lambda context: self.menu_handler.main_menu(context.telegram_id),
            SystemButtons.CHATID: lambda context: self.system_handler.chatid(context.telegram_id),
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

    @staticmethod
    def _summarize_command(text: str) -> str:
        """Сводит пользовательский ввод к безопасному краткому виду."""

        command = text.split(maxsplit=1)[0] if text else ""
        if len(command) > 64:
            command = command[:64]
        return f"{command!r} (len={len(text)})"


TelegramHandlers = CommandRouter
