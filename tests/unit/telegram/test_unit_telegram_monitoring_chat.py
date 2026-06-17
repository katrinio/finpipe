from typing import cast

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.client import TelegramClient
from src.storage.dependencies import StorageDependencies
from src.storage.orm import AllowedUser, UserRole
from src.storage.orm.database import Database
from tests.fakes.fake_storage import FakeStorage, FakeTelegramUpdateStorage
from tests.fakes.fake_telegram import FakeTelegramClient
from tests.helpers.database import build_test_database_url, initialize_test_database


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


def test_monitoring_chat_status_command_stays_in_monitoring_flow(monkeypatch) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")

    telegram_client = FakeTelegramClient()
    bot = TelegramBot(cast(StorageDependencies, FakeStorage({123})), telegram=cast(TelegramClient, telegram_client))
    bot.update_storage = FakeTelegramUpdateStorage()

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

    assert telegram_client.sent_messages_with_chat_ids[-1][0] == -100123
    assert telegram_client.sent_messages_with_chat_ids[-1][1].startswith("📊 Finpipe status")
    assert telegram_client.sent_messages[-1] != "🫥 Неизвестная команда."
    assert bot.update_storage.processed == [32]


def test_user_chat_continues_to_use_user_router(monkeypatch) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")

    database = Database(build_test_database_url())
    initialize_test_database(database)
    AllowedUser.create(123, "alice", UserRole.USER)

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
