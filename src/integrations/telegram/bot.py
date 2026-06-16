"""Локальный Telegram listener и обработчик команд."""

import time

from scripts.bootstrap_allowed_users import bootstrap_primary_admin
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.handlers.command_router import CommandRouter
from src.integrations.telegram.handlers.state_handlers import StateHandler
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.buttons import PUBLIC_COMMANDS
from src.integrations.telegram.ui.menu.admin_menu import build_users_menu
from src.integrations.telegram.ui.menu.document_menu import build_invoice_menu
from src.integrations.telegram.ui.menu.guest_menu import build_guest_menu
from src.integrations.telegram.ui.menu.menu import build_main_menu
from src.integrations.telegram.ui.menu.profile_menu import build_profile_menu, build_signature_menu
from src.integrations.telegram.ui.messages import CommonMessages
from src.logging_config import configure_logging
from src.services.known_user_service import KnownUserService
from src.services.monitoring.event_logger import EventLogger
from src.storage.dependencies import (
    StorageDependencies,
    build_storage_dependencies,
)
from src.storage.orm import AllowedUser
from src.storage.orm.system.app_events import EventSeverity, EventType
from src.storage.orm.system.telegram_update import TelegramUpdate
from src.utils.credentials import LOGGER


class TelegramBot:
    """Telegram listener и обработчик команд."""

    def __init__(
        self,
        storage_dependencies: StorageDependencies,
        telegram: TelegramClient | None = None,
    ) -> None:
        self._telegram = telegram or TelegramClient()
        self.dependencies = storage_dependencies
        self.update_storage = TelegramUpdate
        self.handlers = CommandRouter(
            telegram=self._telegram,
            audit_log=self.dependencies.audit_log,
        )

        self._state_handlers: dict[UserState, StateHandler] = {
            UserState.WAITING_SIGNATURE_UPLOAD: StateHandler(
                handler=self.handlers.signature_handler.handle_signature_upload,
                error_message="✍️ Пришлите подпись в PNG формате.",
            ),
            UserState.WAITING_PROFILE_TEMPLATE_UPLOAD: StateHandler(
                handler=self.handlers.profile_handler.handle_profile_template_upload,
                error_message="📄 Пришлите заполненный шаблон в YAML формате.",
            ),
            UserState.WAITING_INVOICE_AMOUNT: StateHandler(
                handler=self.handlers.document_handler.handle_invoice_amount_input,
                error_message="❌ Сумма должна содержать только цифры.\nПример: 1500",
            ),
            UserState.WAITING_NEW_USER_ID: StateHandler(
                handler=self.handlers.owner_handler.handle_add_user_input,
                error_message="Введите Telegram ID пользователя, состоящий только из цифр.",
            ),
            UserState.WAIT_CONFIRM_ADD_USER: StateHandler(
                handler=self.handlers.owner_handler.confirm_add_user,
                error_message="Используйте кнопки подтверждения ниже.",
            ),
            UserState.WAITING_NEW_USER_CONFIRMATION: StateHandler(
                handler=self.handlers.owner_handler.confirm_add_user,
                error_message="Используйте кнопки подтверждения ниже.",
            ),
            UserState.WAITING_REMOVE_USER_ID: StateHandler(
                handler=self.handlers.owner_handler.handle_remove_user_input,
                error_message="Введите Telegram ID пользователя, состоящий только из цифр.",
            ),
            UserState.WAIT_CONFIRM_REMOVE_USER: StateHandler(
                handler=self.handlers.owner_handler.confirm_remove_user,
                error_message="Используйте кнопки подтверждения ниже.",
            ),
        }

    @property
    def telegram(self) -> TelegramClient:
        return self._telegram

    # polling
    def poll(self) -> int:
        """Получает и обрабатывает новые Telegram updates."""

        last_processed_update_id = self.update_storage.get_last_processed_update_id()

        offset = last_processed_update_id + 1 if last_processed_update_id is not None else None

        updates = self.telegram.get_updates(offset=offset)

        result = updates.get("result", [])

        if result:
            LOGGER.info("Telegram poll returned %s updates", len(result))

        if not result:
            return 0

        if last_processed_update_id is None:
            return self.mark_initial_updates_as_processed(result)

        processed_count = 0

        for update in result:
            try:
                self.process_update(update)
            except Exception:
                update_id = update.get("update_id")
                LOGGER.exception("Failed to process Telegram update %s", update_id)

                EventLogger.log(
                    EventType.ERROR,
                    EventSeverity.ERROR,
                    {"category": "telegram", "update_id": update_id},
                )

        return processed_count

    # update extraction
    def extract_message_data(self, update: dict) -> tuple[str | None, int, str | None] | None:
        """Извлекает текст, пользователя и команду из update."""

        message = update.get("message")
        if not message:
            return None

        text = message.get("text")
        user = message.get("from", {})

        telegram_id = user.get("id")
        if telegram_id is None:
            return None

        return text, telegram_id, user.get("username")

    def extract_callback_data(self, update: dict) -> tuple[str | None, int, str | None] | None:
        """Извлекает callback-кнопку Telegram."""

        callback_query = update.get("callback_query")
        if not callback_query:
            return None

        data = callback_query.get("data")
        user = callback_query.get("from", {})
        telegram_id = user.get("id")
        if telegram_id is None:
            return None

        return data, telegram_id, user.get("username")

    def extract_document_upload_data(self, update: dict) -> tuple[str, int, str, bytes] | None:
        """Извлекает данные файла из Telegram update."""

        message = update.get("message")
        if not message:
            return None

        document = message.get("document")
        if document is not None:
            file_id = document.get("file_id")
            file_name = document.get("file_name")
            file_size = document.get("file_size")
            if file_id and file_name and file_size is not None:
                return file_name, int(file_size), file_id, b""

        photo = message.get("photo")
        if photo:
            last_photo = photo[-1]
            file_id = last_photo.get("file_id")
            file_size = last_photo.get("file_size")
            if file_id and file_size is not None:
                return "signature.png", int(file_size), file_id, b""

        return None

    # state processing
    def _process_waiting_state(self, telegram_id: int, update: dict) -> bool:
        """Обрабатывает upload-состояния без дублирования логики."""

        state_name = UserStateService.get_state(telegram_id)
        if state_name is None:
            return False

        try:
            state = UserState(state_name)
        except ValueError:
            return False

        state_handler = self._state_handlers.get(state)
        if state_handler is None:
            return False

        data = self.extract_message_data(update)
        if data is not None:
            text, _, _ = data

            if state in {
                UserState.WAITING_INVOICE_AMOUNT,
                UserState.WAITING_NEW_USER_ID,
                UserState.WAITING_NEW_USER_CONFIRMATION,
                UserState.WAIT_CONFIRM_ADD_USER,
                UserState.WAITING_REMOVE_USER_ID,
                UserState.WAIT_CONFIRM_REMOVE_USER,
            }:
                if text in self.handlers._command_handlers:
                    LOGGER.info("Cancelling state %s for Telegram user %s", state.name, telegram_id)

                    UserStateService.clear_state(telegram_id)
                    self.telegram.send_message(
                        telegram_id,
                        CommonMessages.Actions.OPERATION_CANCELLED,
                        reply_markup=build_main_menu(is_owner=AllowedUser.is_owner(telegram_id)),
                    )

                    return False

                LOGGER.info("Processing state %s for Telegram user %s", state.name, telegram_id)
                state_handler.handler(telegram_id, text)
                self.update_storage.mark_processed(update["update_id"])
                return True

            if text in self.handlers._command_handlers:
                LOGGER.info("Cancelling state %s for Telegram user %s", state.name, telegram_id)

                UserStateService.clear_state(telegram_id)
                self.telegram.send_message(
                    telegram_id,
                    CommonMessages.Actions.OPERATION_CANCELLED,
                    reply_markup=build_main_menu(is_owner=AllowedUser.is_owner(telegram_id)),
                )

                return False

        LOGGER.info("Processing state %s for Telegram user %s", state.name, telegram_id)

        file_data = self.extract_document_upload_data(update)
        if file_data is None:
            self.telegram.send_message(
                telegram_id,
                state_handler.error_message,
                reply_markup=self._build_state_navigation_menu(telegram_id, state),
            )
            self.update_storage.mark_processed(update["update_id"])
            return True

        file_name, file_size, file_id, _ = file_data

        LOGGER.info("Received upload: file=%s size=%s state=%s", file_name, file_size, state.name)

        file_path = self.telegram.get_file(file_id)
        file_bytes = self.telegram.download_file(file_path)

        state_handler.handler(
            telegram_id,
            file_name,
            file_size,
            file_bytes,
        )

        LOGGER.info("Successfully processed upload for Telegram user %s", telegram_id)

        self.update_storage.mark_processed(update["update_id"])
        return True

    def _build_state_navigation_menu(self, telegram_id: int, state: UserState) -> dict:
        if state == UserState.WAITING_SIGNATURE_UPLOAD:
            return build_signature_menu()
        if state == UserState.WAITING_PROFILE_TEMPLATE_UPLOAD:
            return build_profile_menu()
        if state == UserState.WAITING_INVOICE_AMOUNT:
            return build_invoice_menu()
        if state in {
            UserState.WAITING_NEW_USER_ID,
            UserState.WAITING_NEW_USER_CONFIRMATION,
            UserState.WAIT_CONFIRM_ADD_USER,
            UserState.WAITING_REMOVE_USER_ID,
            UserState.WAIT_CONFIRM_REMOVE_USER,
        }:
            return build_users_menu()
        return build_main_menu(is_owner=AllowedUser.is_owner(telegram_id))

    # authorization and routing
    def process_update(self, update: dict) -> None:
        """Обрабатывает один Telegram update."""

        self._register_known_user(update)
        data = self.extract_message_data(update) or self.extract_callback_data(update)
        if data is None:
            return

        text, telegram_id, username = data

        if not self.is_authorized(telegram_id, text):
            LOGGER.warning("Access denied for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, CommonMessages.Errors.ACCESS_DENIED, reply_markup=build_guest_menu())
            self.update_storage.mark_processed(update["update_id"])
            return

        LOGGER.info("Authorized Telegram user %s", telegram_id)

        if self._process_waiting_state(telegram_id=telegram_id, update=update):
            return

        if text is None:
            self.update_storage.mark_processed(update["update_id"])
            return

        LOGGER.info(
            "Processing Telegram command %s from user %s",
            self._summarize_command(text),
            telegram_id,
        )

        try:
            self.handle_message(text=text, telegram_id=telegram_id, username=username)
        finally:
            self.update_storage.mark_processed(update["update_id"])

    def handle_message(self, text: str, telegram_id: int | None, username: str | None) -> bool:
        """Делегирует команду вынесенным handlers, сохраняя совместимый API."""

        return self.handlers.handle_message(text=text, telegram_id=telegram_id, username=username)

    def _register_known_user(self, update: dict) -> None:
        """Регистрирует Telegram-пользователя при любом входящем update."""

        message = update.get("message")
        if not message:
            return

        user = message.get("from", {})
        telegram_id = user.get("id")
        if telegram_id is None:
            return

        KnownUserService.register_interaction(
            telegram_id=telegram_id,
            username=user.get("username"),
            first_name=user.get("first_name"),
        )

    def mark_initial_updates_as_processed(self, updates: list[dict]) -> int:
        """Первый запуск: сохраняем старые updates без обработки."""
        for update in updates:
            self.update_storage.mark_processed(update["update_id"])
        return len(updates)

    # authorization
    def is_authorized(self, telegram_id: int, text: str | None) -> bool:
        if text in PUBLIC_COMMANDS:
            return True
        return AllowedUser.exists(telegram_id)

    @staticmethod
    def _summarize_command(text: str) -> str:
        """Возвращает безопасное краткое описание пользовательского ввода."""

        command = text.split(maxsplit=1)[0] if text else ""
        if len(command) > 64:
            command = command[:64]
        return f"{command!r} (len={len(text)})"


def main() -> None:
    """Точка входа для Telegram listener."""

    configure_logging()
    storage = build_storage_dependencies()
    bootstrap_primary_admin()
    bot = TelegramBot(storage)

    LOGGER.info("Starting Telegram listener loop")
    while True:
        try:
            bot.poll()
        except Exception:
            LOGGER.exception("Telegram listener iteration failed")
            time.sleep(5)
        time.sleep(1)


if __name__ == "__main__":
    main()
