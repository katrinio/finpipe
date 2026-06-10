from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.commands import BotInfo
from src.integrations.telegram.ui.buttons import OwnerButtons, SystemButtons
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import AllowedUser
from tests.fakes.fake_telegram import FakeTelegramClient


class TestTelegramBot:
    def test_owner_has_access_without_allowlist_entry(
        self,
        fake_telegram_client: Callable[..., FakeTelegramClient],
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
        monkeypatch.setattr(AllowedUser, "exists", classmethod(lambda cls, telegram_id: False))

        bot = TelegramBot(build_storage_dependencies(tmp_path / "storage.sqlite3"), telegram=fake_telegram_client())

        assert bot.is_authorized(777) is True

    def test_allowlisted_user_has_access(
        self,
        fake_telegram_client: Callable[..., FakeTelegramClient],
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
        storage = build_storage_dependencies(tmp_path / "storage.sqlite3")
        AllowedUser.create(123, "alice")

        bot = TelegramBot(storage, telegram=fake_telegram_client())

        assert bot.is_authorized(123) is True

    def test_non_authorized_user_gets_access_denied(
        self,
        caplog: pytest.LogCaptureFixture,
        fake_telegram_client: Callable[..., FakeTelegramClient],
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
        monkeypatch.setattr(AllowedUser, "exists", classmethod(lambda cls, telegram_id: False))

        telegram_client = fake_telegram_client(
            {
                "result": [
                    {
                        "update_id": 11,
                        "message": {
                            "text": SystemButtons.WHOAMI,
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
                    "text": SystemButtons.WHOAMI,
                    "from": {"id": 999, "username": "intruder"},
                },
            }
        )

        assert "Access denied for Telegram user 999 (@intruder)" in caplog.text
        assert telegram_client.sent_messages == [BotInfo.ACCESS_DENIED]

    def test_owner_can_add_user_to_allowlist(
        self,
        fake_telegram_client: Callable[..., FakeTelegramClient],
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")

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
        bot = TelegramBot(build_storage_dependencies(tmp_path / "storage.sqlite3"), telegram=telegram_client)

        bot.process_update(
            {
                "update_id": 11,
                "message": {
                    "text": f"{OwnerButtons.ADD_USER} 123456789",
                    "from": {"id": 777, "username": "owner"},
                },
            }
        )

        assert AllowedUser.exists(123456789) is True
        assert telegram_client.sent_messages == ["✅ Пользователь добавлен."]
