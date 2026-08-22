from typing import Any, cast

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.handlers.state_handlers import StateHandler
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from tests.fakes.fake_storage import FakeTelegramUpdateStorage
from tests.fakes.fake_telegram import FakeTelegramClient


def test_poll_marks_unknown_updates_processed_and_returns_processed_count() -> None:
    telegram = FakeTelegramClient(
        updates={
            "result": [
                {"update_id": 11, "poll_answer": {"poll_id": "first"}},
                {"update_id": 12, "chat_member": {"status": "member"}},
            ]
        }
    )
    bot = TelegramBot(telegram=cast(TelegramClient, telegram), owner_telegram_id=123)
    update_storage = FakeTelegramUpdateStorage()
    bot.update_storage = cast(Any, update_storage)

    assert bot.poll() == 2
    assert update_storage.processed == [11, 12]


def test_poll_stops_at_failed_update_and_does_not_checkpoint_later_update() -> None:
    telegram = FakeTelegramClient(
        updates={
            "result": [
                {"update_id": 11, "message": {"text": "/first", "from": {"id": 123}}},
                {"update_id": 12, "message": {"text": "/second", "from": {"id": 123}}},
            ]
        }
    )
    bot = TelegramBot(telegram=cast(TelegramClient, telegram), owner_telegram_id=123)
    update_storage = FakeTelegramUpdateStorage()
    bot.update_storage = cast(Any, update_storage)
    calls: list[str] = []
    first_attempt = True

    def handle_message(text: str, telegram_id: int | None, username: str | None) -> bool:
        nonlocal first_attempt
        calls.append(text)
        if first_attempt:
            first_attempt = False
            return False
        return True

    bot.handle_message = handle_message

    assert bot.poll() == 0
    assert calls == ["/first"]
    assert update_storage.processed == []

    assert bot.poll() == 2
    assert calls == ["/first", "/first", "/second"]
    assert update_storage.processed == [11, 12]


def test_poll_stops_at_failed_persisted_upload_before_later_update() -> None:
    telegram = FakeTelegramClient(
        updates={
            "result": [
                {
                    "update_id": 11,
                    "message": {
                        "document": {"file_id": "bank", "file_name": "bank.pdf", "file_size": 10},
                        "from": {"id": 123},
                    },
                },
                {"update_id": 12, "message": {"text": "/start", "from": {"id": 123}}},
            ]
        },
        files={"bank": b"%PDF-test"},
    )
    bot = TelegramBot(telegram=cast(TelegramClient, telegram), owner_telegram_id=123)
    update_storage = FakeTelegramUpdateStorage()
    bot.update_storage = cast(Any, update_storage)
    UserStateService.set_state(123, UserState.WAITING_BANK_DOCUMENT_UPLOAD)

    def fail_upload(*args: object) -> None:
        raise RuntimeError("temporary failure")

    bot._state_handlers[UserState.WAITING_BANK_DOCUMENT_UPLOAD] = StateHandler(
        handler=fail_upload,
        error_message="send PDF",
    )

    assert bot.poll() == 0
    assert update_storage.processed == []
    assert UserStateService.get_state(123) == UserState.WAITING_BANK_DOCUMENT_UPLOAD
