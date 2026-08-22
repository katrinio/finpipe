from collections.abc import Callable

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.states import UserState
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


def test_non_owner_cannot_use_callback_or_change_persisted_state(
    fake_telegram_client: Callable[..., FakeTelegramClient],
) -> None:
    telegram = fake_telegram_client()
    bot = TelegramBot(telegram=telegram, owner_telegram_id=777)
    UserStateStorage.upsert(owner_telegram_id=999, state=UserState.WAITING_SIGNATURE_UPLOAD)

    bot.process_update(
        {
            "update_id": 12,
            "callback_query": {
                "data": "delete signature",
                "from": {"id": 999, "username": "intruder"},
            },
        }
    )

    state = UserStateStorage.get_by_owner(999)
    assert state is not None
    assert state.state == UserState.WAITING_SIGNATURE_UPLOAD
    assert UserConfig.get_by_owner(999) is None
    assert TelegramUpdate.is_processed(12) is True


def test_non_owner_update_is_checkpointed_when_denial_delivery_fails() -> None:
    class FailingTelegramClient(FakeTelegramClient):
        def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None) -> None:
            raise RuntimeError("Telegram unavailable")

    bot = TelegramBot(telegram=FailingTelegramClient(), owner_telegram_id=777)
    bot.process_update({"update_id": 13, "message": {"text": "/start", "from": {"id": 999}}})

    assert TelegramUpdate.is_processed(13) is True
