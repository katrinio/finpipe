from collections.abc import Callable
from dataclasses import dataclass

from src.integrations.telegram.buttons import (
    DocumentsMenuButtons,
    InvoiceMenuButtons,
    MainMenuButtons,
    NavigationButtons,
    ProfileButtons,
    SignatureButtons,
    SystemButtons,
)
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import Cmd
from src.integrations.telegram.handlers.document_handlers import DocumentHandlers
from src.integrations.telegram.handlers.menu_handlers import MenuHandler
from src.integrations.telegram.handlers.profile_handlers import ProfileHandlers
from src.integrations.telegram.handlers.signature_handlers import SignatureHandlers
from src.integrations.telegram.handlers.system_handlers import SystemHandlers
from src.integrations.telegram.messages import CommonMessages
from src.integrations.telegram.messages.menu_messages import MenuMessages
from src.integrations.telegram.state_service import UserStateService
from src.utils.credentials import LOGGER


@dataclass(frozen=True)
class CommandContext:
    """Контекст Telegram-команды."""

    telegram_id: int
    username: str | None


class CommandRouter:
    """Маршрутизатор Telegram-команд."""

    def __init__(self, telegram: TelegramClient):
        self.telegram = telegram
        self.state_service = UserStateService()
        self.menu_handler = MenuHandler(self.telegram)
        self.system_handler = SystemHandlers(self.telegram)
        self.document_handler = DocumentHandlers(self.telegram)
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
        )

        try:
            handler = self._command_handlers.get(text)

            if handler is None:
                self.telegram.send_message(context.telegram_id, CommonMessages.Errors.NO_SUCH_COMMAND)
            else:
                handler(context)

        except Exception:
            LOGGER.exception(
                "Command failed for telegram user %s: %s",
                context.telegram_id,
                self._summarize_command(text),
            )
            self.telegram.send_message(context.telegram_id, CommonMessages.Errors.SYSTEM_ERROR)

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
            MainMenuButtons.PROFILE: lambda context: self.menu_handler.settings_menu(context.telegram_id),
            MainMenuButtons.SYSTEM: lambda context: self.menu_handler.system_menu(context.telegram_id),
            NavigationButtons.HOME: lambda context: self.menu_handler.main_menu(context.telegram_id),
            MenuMessages.MAIN_MENU: lambda context: self.menu_handler.main_menu(context.telegram_id),
            # documents
            DocumentsMenuButtons.SALARY_INVOICE: lambda context: self.menu_handler.invoice_menu(context.telegram_id),
            DocumentsMenuButtons.CONVERSION_REQUEST: lambda context: self.document_handler.conversion_request(context.telegram_id),
            DocumentsMenuButtons.BANK_TRANSFER_CONFIRMATION: lambda context: self.document_handler.start_bank_document_upload(context.telegram_id),
            # invoice
            InvoiceMenuButtons.SET_INVOICE_AMOUNT: lambda context: self.document_handler.start_invoice_amount_input(context.telegram_id),
            InvoiceMenuButtons.GET_INVOICE_AMOUNT: lambda context: self.document_handler.get_invoice_amount(context.telegram_id),
            InvoiceMenuButtons.GENERATE_INVOICE: lambda context: self.document_handler.invoice(context.telegram_id),
            # profile
            ProfileButtons.DOWNLOAD_TEMPLATE: lambda context: self.profile_handler.download_template(context.telegram_id),
            ProfileButtons.UPLOAD_TEMPLATE: lambda context: self.profile_handler.upload_template(context.telegram_id),
            ProfileButtons.MY_PROFILE: lambda context: self.profile_handler.show_profile(context.telegram_id),
            # signature
            SignatureButtons.SIGNATURE_UPLOAD: lambda context: self.signature_handler.upload_signature(context.telegram_id),
            SignatureButtons.SIGNATURE_DELETE: lambda context: self.signature_handler.delete_signature(context.telegram_id),
            # system
            SystemButtons.WHOAMI: lambda context: self.system_handler.whoami(context.telegram_id, context.username),
            SystemButtons.CHATID: lambda context: self.system_handler.chatid(context.telegram_id),
            SystemButtons.EASY_START: lambda context: self.system_handler.easy_start(context.telegram_id),
            SystemButtons.READINESS: lambda context: self.system_handler.readiness(context.telegram_id),
        }

    @staticmethod
    def _summarize_command(text: str) -> str:
        """Сводит пользовательский ввод к безопасному краткому виду."""

        command = text.split(maxsplit=1)[0] if text else ""
        if len(command) > 64:
            command = command[:64]
        return f"{command!r} (len={len(text)})"
