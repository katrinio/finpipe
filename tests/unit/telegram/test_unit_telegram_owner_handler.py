from __future__ import annotations

from pathlib import Path

from src.integrations.telegram.handlers.owner_handler import OwnerHandlers
from src.integrations.telegram.ui.menu.guest_menu import build_guest_menu
from src.integrations.telegram.ui.messages import BotInfo
from src.storage.orm import AllowedUser, KnownUser, UserRole
from src.storage.orm.database import Database, build_sqlite_url
from tests.fakes.fake_telegram import FakeTelegramClient


def test_add_user_is_available_only_for_owner(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    AllowedUser.create(1, "owner", UserRole.OWNER)
    KnownUser.upsert(telegram_id=2, username="target", first_name="Target")

    telegram = FakeTelegramClient()
    handlers = OwnerHandlers(telegram)

    handlers.add_user(telegram_id=1, command="/add_user 2")

    assert AllowedUser.exists(2) is True
    assert telegram.sent_messages == [
        "✅ Пользователь добавлен.",
        "✅ Администратор добавил вас в список пользователей.",
    ]
    assert telegram.sent_messages_with_chat_ids == [
        (1, "✅ Пользователь добавлен."),
        (2, "✅ Администратор добавил вас в список пользователей."),
    ]


def test_add_user_denies_non_owner(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    AllowedUser.create(1, "user", UserRole.USER)

    telegram = FakeTelegramClient()
    handlers = OwnerHandlers(telegram)

    handlers.add_user(telegram_id=1, command="/add_user 2")

    assert AllowedUser.exists(2) is False
    assert telegram.sent_messages == [BotInfo.ACCESS_DENIED]
    assert telegram.sent_messages_with_chat_ids == [(1, BotInfo.ACCESS_DENIED)]
    assert telegram.sent_message_payloads == [(1, BotInfo.ACCESS_DENIED, build_guest_menu())]


def test_add_user_denies_unknown_known_user(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    AllowedUser.create(1, "owner", UserRole.OWNER)

    telegram = FakeTelegramClient()
    handlers = OwnerHandlers(telegram)

    handlers.add_user(telegram_id=1, command="/add_user 999")

    assert AllowedUser.exists(999) is False
    assert telegram.sent_messages == [
        "❌ Пользователь ещё не взаимодействовал с ботом.\nПопросите пользователя открыть бота и нажать /start.",
    ]


def test_remove_user_revokes_only_allowlist_access(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    AllowedUser.create(1, "owner", UserRole.OWNER)
    AllowedUser.create(2, "target", UserRole.USER)
    KnownUser.upsert(telegram_id=2, username="target", first_name="Target")

    telegram = FakeTelegramClient()
    handlers = OwnerHandlers(telegram)

    handlers.remove_user(telegram_id=1, command="/remove_user 2")

    assert AllowedUser.exists(2) is False
    assert KnownUser.get_by_telegram_id(2) is not None
    assert telegram.sent_messages == ["✅ Доступ пользователя отозван."]


def test_list_users_uses_known_user_labels(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    AllowedUser.create(1, "owner", UserRole.OWNER)
    AllowedUser.create(2, "target", UserRole.USER)
    KnownUser.upsert(telegram_id=1, username="owner", first_name="Owner")
    KnownUser.upsert(telegram_id=2, username=None, first_name="John")

    telegram = FakeTelegramClient()
    handlers = OwnerHandlers(telegram)

    handlers.list_users(telegram_id=1)

    assert telegram.sent_messages == [
        "📋 Список пользователей\n\n✔️ @owner (1)\n✔️ John (2)",
    ]
