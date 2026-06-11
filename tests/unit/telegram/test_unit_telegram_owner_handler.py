from __future__ import annotations

from pathlib import Path

from src.integrations.telegram.handlers.owner_handler import OwnerHandlers
from src.integrations.telegram.ui.menu.guest_menu import build_guest_menu
from src.integrations.telegram.ui.messages import BotInfo
from src.storage.orm import AllowedUser, UserRole
from src.storage.orm.database import Database, build_sqlite_url
from tests.fakes.fake_telegram import FakeTelegramClient


def test_add_user_is_available_only_for_owner(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    AllowedUser.create(1, "owner", UserRole.OWNER)

    telegram = FakeTelegramClient()
    handlers = OwnerHandlers(telegram)

    handlers.add_user(telegram_id=1, command="/add_user 2", username="owner")

    assert AllowedUser.exists(2) is True
    assert telegram.sent_messages == ["✅ Пользователь добавлен."]
    assert telegram.sent_messages_with_chat_ids == [(1, "✅ Пользователь добавлен.")]


def test_add_user_denies_non_owner(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    AllowedUser.create(1, "user", UserRole.USER)

    telegram = FakeTelegramClient()
    handlers = OwnerHandlers(telegram)

    handlers.add_user(telegram_id=1, command="/add_user 2", username="user")

    assert AllowedUser.exists(2) is False
    assert telegram.sent_messages == [BotInfo.ACCESS_DENIED]
    assert telegram.sent_messages_with_chat_ids == [(1, BotInfo.ACCESS_DENIED)]
    assert telegram.sent_message_payloads == [(1, BotInfo.ACCESS_DENIED, build_guest_menu())]
