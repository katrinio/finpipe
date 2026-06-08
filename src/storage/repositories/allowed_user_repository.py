"""Репозиторий разрешённых Telegram-пользователей."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.storage.orm import AllowedUser


class AllowedUserRepository(Protocol):
    """Доступ к разрешённым Telegram-пользователям."""

    def get_by_telegram_id(self, telegram_id: int) -> AllowedUser | None:
        """Возвращает разрешённого пользователя по Telegram id."""

    def add(self, telegram_id: int, user_name: str) -> None:
        """Добавляет разрешённого пользователя."""

    def list_all(self) -> list[AllowedUser]:
        """Возвращает всех разрешённых пользователей."""


class SQLAlchemyAllowedUserRepository(AllowedUserRepository):
    """SQLAlchemy-репозиторий для `AllowedUser`."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def get_by_telegram_id(self, telegram_id: int) -> AllowedUser | None:
        with self._session_factory() as session:
            statement = select(AllowedUser).where(AllowedUser.telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    def add(self, telegram_id: int, user_name: str) -> None:
        with self._session_factory() as session:
            existing_user = self.get_by_telegram_id(telegram_id)
            if existing_user is not None:
                return

            session.add(AllowedUser(telegram_id=telegram_id, user_name=user_name))
            session.commit()

    def list_all(self) -> list[AllowedUser]:
        with self._session_factory() as session:
            statement = select(AllowedUser).order_by(AllowedUser.telegram_id)
            return list(session.scalars(statement))
