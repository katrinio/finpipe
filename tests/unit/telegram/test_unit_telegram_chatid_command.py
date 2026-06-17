from pathlib import Path

from src.integrations.telegram.buttons.system import SystemButtons
from src.integrations.telegram.handlers.command_router import CommandRouter
from src.storage.orm import AllowedUser, UserRole
from src.storage.orm.database import Database
from src.storage.orm.system.audit_log import AuditLog
from tests.fakes.fake_telegram import FakeTelegramClient
from tests.helpers.database import build_test_database_url, initialize_test_database


def _build_router(telegram: FakeTelegramClient) -> CommandRouter:
    return CommandRouter(telegram=telegram, audit_log=AuditLog)


def test_chatid_is_available_to_owner(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_USERNAME", "owner")
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    AllowedUser.create(777, "owner", UserRole.OWNER)

    telegram = FakeTelegramClient()
    router = _build_router(telegram)

    assert router.handle_message(SystemButtons.CHATID, telegram_id=777, username="owner") is True
    assert telegram.sent_messages_with_chat_ids[-1] == (777, "Chat ID: 777")


def test_chatid_is_hidden_from_non_owner(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_USERNAME", "owner")
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    AllowedUser.create(123, "alice", UserRole.USER)

    telegram = FakeTelegramClient()
    router = _build_router(telegram)

    assert router.handle_message(SystemButtons.CHATID, telegram_id=123, username="alice") is False
    assert telegram.sent_messages[-1] == "🫥 Неизвестная команда."
