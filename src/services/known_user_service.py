"""Регистрирует Telegram-пользователей, уже открывавших бота."""

import logging

from src.storage.orm.system.known_user import KnownUser

LOGGER = logging.getLogger(__name__)


class KnownUserService:
    """Поддерживает актуальный реестр известных Telegram-пользователей."""

    @classmethod
    def register_interaction(cls, telegram_id: int, username: str | None, first_name: str | None) -> None:
        """Создаёт или обновляет запись пользователя по входящему Telegram update."""

        existing_user = KnownUser.get_by_telegram_id(telegram_id)
        KnownUser.upsert(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
        )

        if existing_user is None:
            LOGGER.info("Known user registered for telegram_id=%s", telegram_id)
            return

        if existing_user.username != username or existing_user.first_name != first_name:
            LOGGER.info("Known user updated for telegram_id=%s", telegram_id)
