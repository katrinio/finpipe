"""Репозиторий пользовательских настроек."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.storage.orm import UserConfig


class UserConfigRepository(Protocol):
    """Доступ к конфигурации пользователя по Telegram id."""

    def get_by_telegram_id(self, telegram_id: int) -> UserConfig | None:
        """Возвращает конфигурацию пользователя или `None`."""


class SQLAlchemyUserConfigRepository(UserConfigRepository):
    """SQLAlchemy-репозиторий для `UserConfig`."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def get_by_telegram_id(self, telegram_id: int) -> UserConfig | None:
        """Возвращает запись пользователя по Telegram id."""

        with self._session_factory() as session:
            statement = select(UserConfig).where(UserConfig.telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    def add(self, telegram_id: int, user_name: str) -> None:
        with self._session_factory() as session:
            statement = select(UserConfig).where(UserConfig.telegram_id == telegram_id).limit(1)

            user = session.execute(statement).scalar_one_or_none()

            if user is None:
                user = UserConfig(
                    telegram_id=telegram_id,
                    user_name=user_name,
                )
                session.add(user)
            else:
                user.user_name = user_name

            session.commit()
