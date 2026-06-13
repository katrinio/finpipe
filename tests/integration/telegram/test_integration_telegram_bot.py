from collections.abc import Callable
from pathlib import Path

import pytest

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.commands import BotInfo
from src.integrations.telegram.ui.buttons import OwnerButtons
from src.integrations.telegram.ui.menu.guest_menu import build_guest_menu
from src.storage.bootstrap_allowed_users import bootstrap_primary_admin
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import AllowedUser, KnownUser
from tests.fakes.fake_telegram import FakeTelegramClient


class TestTelegramBot:
    def test_owner_has_access_without_allowlist_entry(
        self,
        fake_telegram_client: Callable[..., FakeTelegramClient],
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
        monkeypatch.setenv("BOT_OWNER_TELEGRAM_USERNAME", "owner")
        bootstrap_primary_admin(tmp_path / "storage.sqlite3")
        storage = build_storage_dependencies(tmp_path / "storage.sqlite3")

        bot = TelegramBot(storage, telegram=fake_telegram_client())

        assert bot.is_authorized(777, f"{OwnerButtons.ADD_USER} 2") is True

    def test_allowlisted_user_has_access(
        self,
        fake_telegram_client: Callable[..., FakeTelegramClient],
        tmp_path: Path,
    ) -> None:
        storage = build_storage_dependencies(tmp_path / "storage.sqlite3")
        AllowedUser.create(123, "alice")

        bot = TelegramBot(storage, telegram=fake_telegram_client())

        assert bot.is_authorized(123, f"{OwnerButtons.ADD_USER} 2") is True

    def test_non_authorized_user_gets_access_denied(
        self,
        caplog: pytest.LogCaptureFixture,
        fake_telegram_client: Callable[..., FakeTelegramClient],
        tmp_path: Path,
    ) -> None:
        build_storage_dependencies(tmp_path / "storage.sqlite3")
        telegram_client = fake_telegram_client(
            {
                "result": [
                    {
                        "update_id": 11,
                        "message": {
                            "text": OwnerButtons.ADD_USER,
                            "from": {"id": 999, "username": "intruder"},
                        },
                    }
                ]
            }
        )
        bot = TelegramBot(build_storage_dependencies(tmp_path / "storage.sqlite3"), telegram=telegram_client)

        caplog.clear()
        bot.process_update(
            {
                "update_id": 11,
                "message": {
                    "text": OwnerButtons.ADD_USER,
                    "from": {"id": 999, "username": "intruder"},
                },
            }
        )

        assert "Access denied for Telegram user 999" in caplog.text
        assert telegram_client.sent_messages == [BotInfo.ACCESS_DENIED]
        assert telegram_client.sent_messages_with_chat_ids == [(999, BotInfo.ACCESS_DENIED)]
        assert telegram_client.sent_message_payloads == [(999, BotInfo.ACCESS_DENIED, build_guest_menu())]

    def test_guest_whoami_shows_user_info_and_guest_menu(
        self,
        fake_telegram_client: Callable[..., FakeTelegramClient],
        tmp_path: Path,
    ) -> None:
        storage = build_storage_dependencies(tmp_path / "storage.sqlite3")
        telegram_client = fake_telegram_client(
            {
                "result": [
                    {
                        "update_id": 12,
                        "message": {
                            "text": "👤 Кто я",
                            "from": {"id": 999, "username": "intruder"},
                        },
                    }
                ]
            }
        )
        bot = TelegramBot(storage, telegram=telegram_client)

        bot.process_update(
            {
                "update_id": 12,
                "message": {
                    "text": "👤 Кто я",
                    "from": {"id": 999, "username": "intruder"},
                },
            }
        )

        assert telegram_client.sent_messages == [
            "👤 Информация о пользователе\nTelegram ID: 999\nUsername: @intruder",
        ]
        assert telegram_client.sent_message_payloads == [
            (999, "👤 Информация о пользователе\nTelegram ID: 999\nUsername: @intruder", build_guest_menu())
        ]
        known_user = KnownUser.get_by_telegram_id(999)
        assert known_user is not None
        assert known_user.username == "intruder"

    def test_owner_can_add_user_to_allowlist(
        self,
        fake_telegram_client: Callable[..., FakeTelegramClient],
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
        monkeypatch.setenv("BOT_OWNER_TELEGRAM_USERNAME", "owner")
        bootstrap_primary_admin(tmp_path / "storage.sqlite3")
        storage = build_storage_dependencies(tmp_path / "storage.sqlite3")
        KnownUser.upsert(telegram_id=123456789, username="target_user", first_name="Target")

        telegram_client = fake_telegram_client(
            {
                "result": [
                    {
                        "update_id": 11,
                        "message": {
                            "text": f"{OwnerButtons.ADD_USER} 123456789",
                            "from": {"id": 777, "username": "owner"},
                        },
                    }
                ]
            }
        )
        bot = TelegramBot(storage, telegram=telegram_client)

        bot.process_update(
            {
                "update_id": 11,
                "message": {
                    "text": OwnerButtons.ADD_USER,
                    "from": {"id": 777, "username": "owner"},
                },
            }
        )
        bot.process_update(
            {
                "update_id": 12,
                "message": {
                    "text": "123456789",
                    "from": {"id": 777, "username": "owner"},
                },
            }
        )
        bot.process_update(
            {
                "update_id": 13,
                "message": {
                    "text": OwnerButtons.CONFIRM_ADD_USER,
                    "from": {"id": 777, "username": "owner"},
                },
            }
        )

        assert telegram_client.sent_messages == [
            "Введите Telegram ID пользователя, который уже открыл бота.",
            "👤 Пользователь найден\n• @target_user\n• ID: 123456789\nВыдать доступ?",
            "✅ Пользователь добавлен.",
            "✅ Администратор добавил вас в список пользователей.",
        ]
        assert telegram_client.sent_messages_with_chat_ids == [
            (777, "Введите Telegram ID пользователя, который уже открыл бота."),
            (777, "👤 Пользователь найден\n• @target_user\n• ID: 123456789\nВыдать доступ?"),
            (777, "✅ Пользователь добавлен."),
            (123456789, "✅ Администратор добавил вас в список пользователей."),
        ]
        assert AllowedUser.exists(123456789) is True
