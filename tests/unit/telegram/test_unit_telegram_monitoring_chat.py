from typing import cast

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.client import TelegramClient
from src.storage.dependencies import StorageDependencies
from tests.fakes.fake_storage import FakeStorage, FakeTelegramUpdateStorage
from tests.fakes.fake_telegram import FakeTelegramClient


def test_monitoring_chat_message_is_ignored(monkeypatch) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")

    telegram_client = FakeTelegramClient()
    bot = TelegramBot(cast(StorageDependencies, FakeStorage({123})), telegram=cast(TelegramClient, telegram_client))
    bot.update_storage = FakeTelegramUpdateStorage()

    bot.process_update(
        {
            "update_id": 31,
            "message": {
                "text": "/unknown",
                "chat": {"id": -100123, "type": "group"},
                "from": {"id": 123, "username": "alice"},
            },
        }
    )

    assert telegram_client.sent_messages == []
    assert telegram_client.sent_messages_with_chat_ids == []
    assert bot.update_storage.processed == [31]
