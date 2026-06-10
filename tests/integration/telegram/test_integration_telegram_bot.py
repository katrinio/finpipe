from collections.abc import Callable
from typing import cast

import pytest

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import BotInfo
from src.integrations.telegram.ui.buttons import SystemButtons
from src.storage.dependencies import StorageDependencies
from src.storage.orm import AllowedUser
from src.storage.orm.system.telegram_update import TelegramUpdate
from tests.fakes.fake_storage import FakeStorage, FakeTelegramUpdateStorage
from tests.fakes.fake_telegram import FakeTelegramClient


class TestTelegramBot:
    def test_poll_denies_unauthorized_user(
        self,
        caplog: pytest.LogCaptureFixture,
        fake_telegram_client: Callable[..., FakeTelegramClient],
        fake_storage: Callable[[set[int] | None], FakeStorage],
        fake_update_storage: FakeTelegramUpdateStorage,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(AllowedUser, "get_by_telegram_id", classmethod(lambda cls, telegram_id: None))

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
        tg_bot = TelegramBot(cast(StorageDependencies, fake_storage(set())), telegram=cast(TelegramClient, telegram_client))
        tg_bot.update_storage = cast(type[TelegramUpdate], fake_update_storage)

        caplog.clear()
        tg_bot.poll()

        assert "Access denied for Telegram user 999 (@intruder)" in caplog.text
        assert telegram_client.sent_messages == [BotInfo.ACCESS_DENIED]
        assert fake_update_storage.processed == []

    def test_poll_processes_authorized_user_and_whoami(
        self,
        fake_telegram_client: Callable[..., FakeTelegramClient],
        fake_storage: Callable[[set[int] | None], FakeStorage],
        fake_update_storage: FakeTelegramUpdateStorage,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            AllowedUser,
            "get_by_telegram_id",
            classmethod(lambda cls, telegram_id: AllowedUser(telegram_id=telegram_id, user_name="alice")),
        )
        user_name = "alice"
        user_id = 123
        telegram_client = fake_telegram_client(
            {
                "result": [
                    {
                        "update_id": 11,
                        "message": {
                            "text": SystemButtons.WHOAMI,
                            "from": {"id": user_id, "username": user_name},
                        },
                    }
                ]
            }
        )
        tg_bot = TelegramBot(cast(StorageDependencies, fake_storage({user_id})), telegram=cast(TelegramClient, telegram_client))
        tg_bot.update_storage = cast(type[TelegramUpdate], fake_update_storage)

        tg_bot.poll()

        assert telegram_client.sent_messages == [
            f"{BotInfo.WHOAMI_PREFIX}\ntelegram_id: {user_id}\nusername: {user_name}",
        ]
        assert fake_update_storage.processed == [11]
