from pathlib import Path
from typing import Any, cast

import pytest

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.handlers.command_router import CommandRouter
from src.integrations.telegram.handlers.monitoring_handler import MonitoringHandler
from src.storage.dependencies import StorageDependencies
from src.storage.orm import AllowedUser, UserRole
from src.storage.orm.database import Database
from src.storage.orm.system.audit_log import AuditLog
from tests.fakes.fake_storage import FakeStorage, FakeTelegramUpdateStorage
from tests.fakes.fake_telegram import FakeTelegramClient
from tests.helpers.database import build_test_database_url, initialize_test_database


def test_monitoring_chat_status_is_handled_in_monitoring_handler(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    AllowedUser.create(777, "owner", UserRole.OWNER)

    telegram = FakeTelegramClient()
    handler = MonitoringHandler(cast(TelegramClient, telegram))

    handled = handler.handle_message("/status", chat_id=-100123, telegram_id=777, username="owner")

    assert handled is True
    assert telegram.sent_message_payloads[-1][0] == -100123
    assert telegram.sent_message_payloads[-1][1].startswith("📊 Finpipe status")


def test_monitoring_chat_command_does_not_go_to_user_router(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    AllowedUser.create(777, "owner", UserRole.OWNER)

    telegram = FakeTelegramClient()
    bot = TelegramBot(cast(StorageDependencies, FakeStorage({777})), telegram=cast(TelegramClient, telegram))
    bot.update_storage = cast(Any, FakeTelegramUpdateStorage())

    bot.process_update(
        {
            "update_id": 40,
            "message": {
                "text": "/status",
                "chat": {"id": -100123, "type": "group"},
                "from": {"id": 777, "username": "owner"},
            },
        }
    )

    assert telegram.sent_messages_with_chat_ids[-1][0] == -100123
    assert telegram.sent_messages_with_chat_ids[-1][1].startswith("📊 Finpipe status")
    update_storage = cast(Any, bot.update_storage)
    assert update_storage.processed == [40]


def test_unknown_monitoring_text_is_ignored(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    AllowedUser.create(777, "owner", UserRole.OWNER)

    telegram = FakeTelegramClient()
    handler = MonitoringHandler(cast(TelegramClient, telegram))

    handled = handler.handle_message("hello", chat_id=-100123, telegram_id=777, username="owner")

    assert handled is True
    assert telegram.sent_messages == []


def test_user_router_does_not_expose_monitoring_commands(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "-100123")
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    AllowedUser.create(777, "owner", UserRole.OWNER)

    telegram = FakeTelegramClient()
    router = CommandRouter(telegram=cast(TelegramClient, telegram), audit_log=AuditLog)

    assert router.handle_message("/status", telegram_id=777, username="owner") is True
    assert telegram.sent_messages[-1] == "🫥 Неизвестная команда."
