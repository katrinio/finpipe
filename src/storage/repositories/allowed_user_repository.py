"""Репозиторий разрешённых Telegram-пользователей."""

from __future__ import annotations

from typing import Protocol

from src.storage.orm import AllowedUser


class AllowedUserRepository(Protocol):
    """Доступ к разрешённым Telegram-пользователям."""

    def get_by_telegram_id(self, telegram_id: int) -> AllowedUser | None:
        """Возвращает разрешённого пользователя по Telegram id."""

    def add(self, telegram_id: int, user_name: str) -> None:
        """Добавляет разрешённого пользователя."""

    def list_all(self) -> list[AllowedUser]:
        """Возвращает всех разрешённых пользователей."""
