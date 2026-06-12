"""Команды владельца Telegram-бота."""

import logging

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.buttons import OwnerButtons
from src.integrations.telegram.ui.menu.admin_menu import (
    build_add_user_confirmation_menu,
    build_remove_user_confirmation_menu,
    build_users_menu,
)
from src.integrations.telegram.ui.menu.guest_menu import build_guest_menu
from src.integrations.telegram.ui.messages import BotInfo
from src.storage.orm import AllowedUser, KnownUser, UserRole

LOGGER = logging.getLogger(__name__)


class OwnerHandlers:
    """Обрабатывает команды владельца бота."""

    _pending_access_grants: dict[int, int] = {}
    _pending_access_revocations: dict[int, int] = {}

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def start_add_user_input(self, telegram_id: int) -> None:
        """Запускает безопасный сценарий выдачи доступа известному пользователю."""

        if not self._ensure_owner(telegram_id):
            return

        UserStateService.set_state(telegram_id, UserState.WAITING_NEW_USER_ID)
        self.telegram.send_message(
            telegram_id,
            "Введите Telegram ID пользователя, который уже открыл бота.",
            reply_markup=build_users_menu(),
        )

    def handle_add_user_input(self, telegram_id: int, text: str | None) -> None:
        """Проверяет KnownUser и подготавливает подтверждение выдачи доступа."""

        if not self._ensure_owner(telegram_id):
            return

        if text is None or not text.isdigit():
            self.telegram.send_message(
                telegram_id,
                "Введите корректный Telegram ID, состоящий только из цифр.",
                reply_markup=build_users_menu(),
            )
            return

        allowed_telegram_id = int(text)
        known_user = KnownUser.get_by_telegram_id(allowed_telegram_id)
        if known_user is None:
            UserStateService.clear_state(telegram_id)
            self.telegram.send_message(
                telegram_id,
                "❌ Пользователь ещё не взаимодействовал с ботом.\nПопросите пользователя открыть бота и нажать /start.",
                reply_markup=build_users_menu(),
            )
            return

        self._pending_access_grants[telegram_id] = allowed_telegram_id
        UserStateService.set_state(telegram_id, UserState.WAIT_CONFIRM_ADD_USER)
        LOGGER.info(
            "User access confirmation requested by admin_telegram_id=%s for target_telegram_id=%s",
            telegram_id,
            allowed_telegram_id,
        )
        self.telegram.send_message(
            telegram_id,
            f"👤 Пользователь найден\n• {self._format_known_user_label(known_user)}\n• ID: {known_user.telegram_id}\nВыдать доступ?",
            reply_markup=build_add_user_confirmation_menu(),
        )

    def confirm_add_user(self, telegram_id: int, text: str | None) -> None:
        """Подтверждает выдачу доступа пользователю из pending state."""

        if not self._ensure_owner(telegram_id):
            return

        pending_telegram_id = self._pending_access_grants.get(telegram_id)
        if pending_telegram_id is None:
            UserStateService.clear_state(telegram_id)
            self.telegram.send_message(
                telegram_id,
                "Нет ожидающего подтверждения на выдачу доступа.",
                reply_markup=build_users_menu(),
            )
            return

        if text == OwnerButtons.CANCEL_ADMIN_ACTION:
            self._pending_access_grants.pop(telegram_id, None)
            UserStateService.clear_state(telegram_id)
            LOGGER.info(
                "Administrative action cancelled by admin_telegram_id=%s for target_telegram_id=%s",
                telegram_id,
                pending_telegram_id,
            )
            self.telegram.send_message(
                telegram_id,
                OwnerButtons.USERS,
                reply_markup=build_users_menu(),
            )
            return

        if text != OwnerButtons.CONFIRM_ADD_USER:
            self.telegram.send_message(telegram_id, "Используйте кнопки подтверждения ниже.", reply_markup=build_add_user_confirmation_menu())
            return

        known_user = KnownUser.get_by_telegram_id(pending_telegram_id)
        if known_user is None:
            self._pending_access_grants.pop(telegram_id, None)
            UserStateService.clear_state(telegram_id)
            self.telegram.send_message(
                telegram_id,
                "❌ Пользователь ещё не взаимодействовал с ботом.\nПопросите пользователя открыть бота и нажать /start.",
                reply_markup=build_users_menu(),
            )
            return

        AllowedUser.upsert(
            telegram_id=pending_telegram_id,
            username=known_user.username,
        )
        LOGGER.info(
            "User access granted by admin_telegram_id=%s for target_telegram_id=%s",
            telegram_id,
            pending_telegram_id,
        )
        self._pending_access_grants.pop(telegram_id, None)
        UserStateService.clear_state(telegram_id)
        self.telegram.send_message(telegram_id, "✅ Пользователь добавлен.", reply_markup=build_users_menu())
        self.telegram.send_message(pending_telegram_id, "✅ Администратор добавил вас в список пользователей.")

    def start_remove_user_input(self, telegram_id: int) -> None:
        """Запускает сценарий удаления пользователя из allowlist."""

        if not self._ensure_owner(telegram_id):
            return

        UserStateService.set_state(telegram_id, UserState.WAITING_REMOVE_USER_ID)
        self.telegram.send_message(
            telegram_id,
            "Введите Telegram ID пользователя, у которого нужно отозвать доступ.",
            reply_markup=build_users_menu(),
        )

    def handle_remove_user_input(self, telegram_id: int, text: str | None) -> None:
        """Удаляет пользователя из allowlist по Telegram ID."""

        if not self._ensure_owner(telegram_id):
            return

        if text is None or not text.isdigit():
            self.telegram.send_message(
                telegram_id,
                "Введите корректный Telegram ID, состоящий только из цифр.",
                reply_markup=build_users_menu(),
            )
            return

        target_telegram_id = int(text)
        if not AllowedUser.exists(target_telegram_id):
            UserStateService.clear_state(telegram_id)
            self.telegram.send_message(
                telegram_id,
                "❌ У пользователя нет доступа или он не найден в списке.",
                reply_markup=build_users_menu(),
            )
            return

        known_user = KnownUser.get_by_telegram_id(target_telegram_id)
        self._pending_access_revocations[telegram_id] = target_telegram_id
        UserStateService.set_state(telegram_id, UserState.WAIT_CONFIRM_REMOVE_USER)
        LOGGER.info(
            "User removal confirmation requested by admin_telegram_id=%s for target_telegram_id=%s",
            telegram_id,
            target_telegram_id,
        )
        self.telegram.send_message(
            telegram_id,
            f"👤 Пользователь найден\n• {self._format_known_user_label(known_user)}\n• ID: {target_telegram_id}\nОтозвать доступ?",
            reply_markup=build_remove_user_confirmation_menu(),
        )

    def confirm_remove_user(self, telegram_id: int, text: str | None) -> None:
        """Подтверждает отзыв доступа пользователя из pending state."""

        if not self._ensure_owner(telegram_id):
            return

        pending_telegram_id = self._pending_access_revocations.get(telegram_id)
        if pending_telegram_id is None:
            UserStateService.clear_state(telegram_id)
            self.telegram.send_message(
                telegram_id,
                "Нет ожидающего подтверждения на отзыв доступа.",
                reply_markup=build_users_menu(),
            )
            return

        if text == OwnerButtons.CANCEL_ADMIN_ACTION:
            self._pending_access_revocations.pop(telegram_id, None)
            UserStateService.clear_state(telegram_id)
            LOGGER.info(
                "Administrative action cancelled by admin_telegram_id=%s for target_telegram_id=%s",
                telegram_id,
                pending_telegram_id,
            )
            self.telegram.send_message(
                telegram_id,
                OwnerButtons.USERS,
                reply_markup=build_users_menu(),
            )
            return

        if text != OwnerButtons.CONFIRM_REMOVE_USER:
            self.telegram.send_message(telegram_id, "Используйте кнопки подтверждения ниже.", reply_markup=build_remove_user_confirmation_menu())
            return

        AllowedUser.delete(pending_telegram_id)
        LOGGER.info(
            "User access revoked by admin_telegram_id=%s for target_telegram_id=%s",
            telegram_id,
            pending_telegram_id,
        )
        self._pending_access_revocations.pop(telegram_id, None)
        UserStateService.clear_state(telegram_id)
        self.telegram.send_message(telegram_id, "✅ Доступ пользователя отозван.", reply_markup=build_users_menu())

    def list_users(self, telegram_id: int) -> None:
        """Показывает всех пользователей с выданным доступом."""

        if not self._ensure_owner(telegram_id):
            return

        allowed_users = AllowedUser.list_all()
        LOGGER.info("Users list requested by telegram_id=%s", telegram_id)
        if not allowed_users:
            self.telegram.send_message(telegram_id, "Список пользователей пуст.")
            return

        lines = ["📋 Список пользователей", ""]
        for allowed_user in allowed_users:
            known_user = KnownUser.get_by_telegram_id(allowed_user.telegram_id)
            label = self._format_known_user_label(known_user, fallback_username=allowed_user.username)
            lines.append(self._format_allowed_user_entry(allowed_user, label))

        self.telegram.send_message(telegram_id, "\n".join(lines))

    def add_user(self, telegram_id: int, command: str) -> None:
        """Совместимый CLI-like сценарий выдачи доступа по `/add_user <telegram_id>`."""

        if not self._ensure_owner(telegram_id):
            return

        parts = command.split()
        if len(parts) != 2:
            self.telegram.send_message(telegram_id, "Использование: /add_user <telegram_id>", reply_markup=build_users_menu())
            return

        try:
            allowed_telegram_id = int(parts[1])
        except ValueError:
            self.telegram.send_message(
                telegram_id,
                "Использование: /add_user <telegram_id>",
                reply_markup=build_users_menu(),
            )
            return

        known_user = KnownUser.get_by_telegram_id(allowed_telegram_id)
        if known_user is None:
            self.telegram.send_message(
                telegram_id,
                "❌ Пользователь ещё не взаимодействовал с ботом.\nПопросите пользователя открыть бота и нажать /start.",
                reply_markup=build_users_menu(),
            )
            return

        AllowedUser.upsert(telegram_id=allowed_telegram_id, username=known_user.username)
        LOGGER.info("Access granted for telegram_id=%s", allowed_telegram_id)

        self.telegram.send_message(telegram_id, "✅ Пользователь добавлен.", reply_markup=build_users_menu())
        self.telegram.send_message(allowed_telegram_id, "✅ Администратор добавил вас в список пользователей.")

    def remove_user(self, telegram_id: int, command: str) -> None:
        """Совместимый CLI-like сценарий отзыва доступа по `/remove_user <telegram_id>`."""

        if not self._ensure_owner(telegram_id):
            return

        parts = command.split()
        if len(parts) != 2:
            self.telegram.send_message(telegram_id, "Использование: /remove_user <telegram_id>")
            return

        try:
            target_telegram_id = int(parts[1])
        except ValueError:
            self.telegram.send_message(telegram_id, "Использование: /remove_user <telegram_id>")
            return

        if not AllowedUser.exists(target_telegram_id):
            self.telegram.send_message(telegram_id, "❌ У пользователя нет доступа или он не найден в списке.")
            return

        AllowedUser.delete(target_telegram_id)
        LOGGER.info(
            "User access revoked by admin_telegram_id=%s for target_telegram_id=%s",
            telegram_id,
            target_telegram_id,
        )
        self.telegram.send_message(telegram_id, "✅ Доступ пользователя отозван.")

    def _ensure_owner(self, telegram_id: int) -> bool:
        if not AllowedUser.is_owner(telegram_id):
            self.telegram.send_message(telegram_id, BotInfo.ACCESS_DENIED, reply_markup=build_guest_menu())
            return False

        return True

    @staticmethod
    def _format_known_user_label(known_user: KnownUser | None, fallback_username: str | None = None) -> str:
        if known_user is not None:
            if known_user.username:
                return f"@{known_user.username}"
            if known_user.first_name:
                return known_user.first_name

        if fallback_username:
            return f"@{fallback_username}"

        return "unknown"

    @staticmethod
    def _format_allowed_user_entry(allowed_user: AllowedUser, label: str) -> str:
        role_prefixes = {
            UserRole.ADMIN: "🛠️ Admin",
            UserRole.OWNER: "👑 Owner",
            UserRole.USER: "✔️ User",
        }
        try:
            role = UserRole(allowed_user.role) if allowed_user.role is not None else UserRole.USER
        except ValueError:
            role = UserRole.USER
        role_prefix = role_prefixes[role]
        return f"{role_prefix} {label} ({allowed_user.telegram_id})"
