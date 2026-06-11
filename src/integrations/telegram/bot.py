"""Локальный Telegram listener и обработчик команд."""

from __future__ import annotations

from src.constants import Dir
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import BotInfo
from src.integrations.telegram.handlers.command_router import CommandRouter
from src.integrations.telegram.handlers.state_handlers import StateHandler
from src.integrations.telegram.settings import TelegramSettings
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.storage.bootstrap_allowed_users import bootstrap_primary_admin
from src.storage.dependencies import (
    StorageDependencies,
    build_storage_dependencies,
)
from src.storage.orm import AllowedUser
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
        }

    @property
    def telegram(self) -> TelegramClient:
        return self._telegram

    def poll(self) -> int:
        """Получает и обрабатывает новые Telegram updates."""

        last_processed_update_id = self.update_storage.get_last_processed_update_id()

        offset = last_processed_update_id + 1 if last_processed_update_id is not None else None

        updates = self.telegram.get_updates(offset=offset)

        result = updates.get("result", [])
        LOGGER.info("Telegram poll returned %s updates", len(result))

        if not result:
            return 0

        if last_processed_update_id is None:
            return self.mark_initial_updates_as_processed(result)

        for update in result:
            self.process_update(update)

        return len(result)

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

            if text in self.handlers._command_handlers:
                LOGGER.info("Cancelling state %s for Telegram user %s", state.name, telegram_id)

                UserStateService.clear_state(telegram_id)
                self.telegram.send_message("Текущая операция отменена.")

                return False

        LOGGER.info("Processing state %s for Telegram user %s", state.name, telegram_id)

        file_data = self.extract_document_upload_data(update)
        if file_data is None:
            self.telegram.send_message(state_handler.error_message)
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

    def process_update(self, update: dict) -> None:
        """Обрабатывает один Telegram update."""

        data = self.extract_message_data(update)
        if data is None:
            return

        text, telegram_id, username = data

        if not self.is_authorized(telegram_id):
            LOGGER.warning("Access denied for Telegram user %s (@%s)", telegram_id, username)
            self.telegram.send_message(BotInfo.ACCESS_DENIED)
            return

        LOGGER.info("Authorized Telegram user %s (@%s)", telegram_id, username)

        if self._process_waiting_state(telegram_id=telegram_id, update=update):
            return

        if text is None:
            self.update_storage.mark_processed(update["update_id"])
            return

        LOGGER.info("Processing Telegram command %r from user %s (@%s)", text, telegram_id, username)

        try:
            self.handle_message(text=text, telegram_id=telegram_id, username=username)
        finally:
            self.update_storage.mark_processed(update["update_id"])

    def handle_message(self, text: str, telegram_id: int | None, username: str | None) -> bool:
        """Делегирует команду вынесенным handlers, сохраняя совместимый API."""

        return self.handlers.handle_message(text=text, telegram_id=telegram_id, username=username)

    def mark_initial_updates_as_processed(self, updates: list[dict]) -> int:
        """Первый запуск: сохраняем старые updates без обработки."""
        for update in updates:
            self.update_storage.mark_processed(update["update_id"])
        return len(updates)

    def is_authorized(self, telegram_id: int) -> bool:
        """Проверяет доступ пользователя."""
        return telegram_id == TelegramSettings.owner_telegram_id() or AllowedUser.exists(telegram_id)


def main() -> None:
    """Точка входа для Telegram listener."""

    bootstrap_primary_admin()
    bot = TelegramBot(build_storage_dependencies(Dir.STORAGE_DB))

    LOGGER.info("Starting Telegram listener loop")
    while True:
        try:
            bot.poll()
        except Exception:
            LOGGER.exception("Telegram listener iteration failed")

        # time.sleep(5)


if __name__ == "__main__":
    main()
