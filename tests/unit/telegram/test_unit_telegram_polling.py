from typing import Any, cast

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.client import TelegramClient
from src.storage.dependencies import StorageDependencies
from tests.fakes.fake_storage import FakeStorage, FakeTelegramUpdateStorage
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
    bot = TelegramBot(cast(StorageDependencies, FakeStorage(set())), telegram=cast(TelegramClient, telegram))
    update_storage = FakeTelegramUpdateStorage()
    bot.update_storage = cast(Any, update_storage)

    assert bot.poll() == 2
    assert update_storage.processed == [11, 12]
