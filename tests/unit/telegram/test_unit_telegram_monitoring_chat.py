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


def test_monitoring_chat_status_command_stays_in_monitoring_flow(monkeypatch, caplog) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")

    telegram_client = FakeTelegramClient()
    bot = TelegramBot(cast(StorageDependencies, FakeStorage({123})), telegram=cast(TelegramClient, telegram_client))
    bot.update_storage = FakeTelegramUpdateStorage()

    with caplog.at_level("INFO"):
        bot.process_update(
            {
                "update_id": 32,
                "message": {
                    "text": "/status",
                    "chat": {"id": -100123, "type": "group"},
                    "from": {"id": 249517409, "username": "owner"},
                },
            }
        )

    assert any("Telegram update: user_id=249517409 chat_id=-100123 chat_type=group text=/status" in record.message for record in caplog.records)
    assert telegram_client.sent_messages_with_chat_ids[-1][0] == -100123
    assert telegram_client.sent_messages_with_chat_ids[-1][1].startswith("📊 Finpipe status")
    assert telegram_client.sent_messages[-1] != "🫥 Неизвестная команда."
    assert bot.update_storage.processed == [32]


def test_user_chat_continues_to_use_user_router(monkeypatch) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")

    telegram_client = FakeTelegramClient()
    bot = TelegramBot(cast(StorageDependencies, FakeStorage({123})), telegram=cast(TelegramClient, telegram_client))
    bot.update_storage = FakeTelegramUpdateStorage()

    bot.process_update(
        {
            "update_id": 33,
            "message": {
                "text": "/unknown",
                "chat": {"id": 777, "type": "private"},
                "from": {"id": 123, "username": "alice"},
            },
        }
    )

    assert telegram_client.sent_messages_with_chat_ids[-1][0] == 123
    assert telegram_client.sent_messages_with_chat_ids[-1][1] == "🫥 Неизвестная команда."
    assert bot.update_storage.processed == [33]
