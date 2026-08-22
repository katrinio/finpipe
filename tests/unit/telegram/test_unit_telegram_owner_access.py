from collections.abc import Callable

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.ui.messages import CommonMessages
from src.storage.orm import TelegramUpdate, UserConfig, UserStateStorage
from tests.fakes.fake_telegram import FakeTelegramClient


def test_configured_owner_is_authorized(fake_telegram_client: Callable[..., FakeTelegramClient]) -> None:
    bot = TelegramBot(telegram=fake_telegram_client(), owner_telegram_id=777)

    assert bot.is_authorized(777) is True
    assert bot.is_authorized(778) is False


def test_non_owner_is_denied_without_persisting_user_data(
    fake_telegram_client: Callable[..., FakeTelegramClient],
) -> None:
    telegram = fake_telegram_client()
    bot = TelegramBot(telegram=telegram, owner_telegram_id=777)

    bot.process_update(
        {
            "update_id": 11,
            "message": {
                "text": "/start",
                "from": {"id": 999, "username": "intruder"},
            },
        }
    )

    assert telegram.sent_message_payloads == [(999, CommonMessages.Errors.ACCESS_DENIED, None)]
    assert UserConfig.get_by_owner(999) is None
    assert UserStateStorage.get_by_owner(999) is None
    assert TelegramUpdate.is_processed(11) is True
