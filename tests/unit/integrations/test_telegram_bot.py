from datetime import datetime
from types import SimpleNamespace

import pytz

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.commands import BotInfo, Cmd
from src.storage.orm import AllowedUser


class FakeTelegramClient:
    def __init__(self, updates: dict | None = None) -> None:
        self.sent_messages: list[str] = []
        self._updates = updates or {"result": []}

    def send_message(self, text: str) -> None:
        self.sent_messages.append(text)

    def get_updates(self, offset: int | None = None) -> dict:
        return self._updates

    def healthcheck(self) -> None:
        return None


class FakeUserConfigRepository:
    def __init__(self, allowed_ids: set[int]) -> None:
        self.allowed_ids = allowed_ids

    def get_by_telegram_id(self, telegram_id: int):
        if telegram_id in self.allowed_ids:
            return SimpleNamespace(telegram_id=telegram_id, user_name="alice")
        return None


class FakeStorage:
    def __init__(self, allowed_ids: set[int]) -> None:
        self.allowed_users = FakeUserConfigRepository(allowed_ids)
        self.audit_log = SimpleNamespace(list_recent=lambda limit=50: [])


class FakeTelegramUpdateStorage:
    def __init__(self) -> None:
        self.processed: list[int] = []

    def get_last_processed_update_id(self) -> int | None:
        return 10

    def mark_processed(self, update_id: int) -> None:
        self.processed.append(update_id)


def test_poll_denies_unauthorized_user(caplog) -> None:
    updates = {
        "result": [
            {
                "update_id": 11,
                "message": {
                    "text": Cmd.STATUS,
                    "from": {"id": 999, "username": "intruder"},
                },
            }
        ]
    }
    telegram_client = FakeTelegramClient(updates)
    update_storage = FakeTelegramUpdateStorage()
    tg_bot = TelegramBot(FakeStorage(set()))

    original_get_by_telegram_id = AllowedUser.get_by_telegram_id
    AllowedUser.get_by_telegram_id = classmethod(lambda cls, telegram_id: None)

    tg_bot.telegram = telegram_client
    tg_bot.update_storage = update_storage

    try:
        caplog.clear()
        tg_bot.poll()

        assert "Access denied for Telegram user 999 (@intruder)" in caplog.text
        assert telegram_client.sent_messages == ["⛔ Access denied"]
        assert update_storage.processed == []
    finally:
        AllowedUser.get_by_telegram_id = original_get_by_telegram_id


def test_poll_processes_authorized_user_and_whoami() -> None:
    updates = {
        "result": [
            {
                "update_id": 11,
                "message": {
                    "text": Cmd.WHOAMI,
                    "from": {"id": 123, "username": "alice"},
                },
            }
        ]
    }
    telegram_client = FakeTelegramClient(updates)
    update_storage = FakeTelegramUpdateStorage()
    tg_bot = TelegramBot(FakeStorage({123}))

    original_get_by_telegram_id = AllowedUser.get_by_telegram_id
    AllowedUser.get_by_telegram_id = classmethod(lambda cls, telegram_id: SimpleNamespace(telegram_id=telegram_id, user_name="alice"))

    tg_bot.telegram = telegram_client
    tg_bot.update_storage = update_storage

    try:
        tg_bot.poll()

        assert telegram_client.sent_messages == [
            f"{BotInfo.WHOAMI_PREFIX}\ntelegram_id: 123\nusername: alice",
        ]
        assert update_storage.processed == [11]
    finally:
        AllowedUser.get_by_telegram_id = original_get_by_telegram_id


def test_handle_message_last_action_uses_storage_audit_log() -> None:

    telegram_client = FakeTelegramClient()
    audit_action = SimpleNamespace(
        user_name="alice",
        command="/invoice",
        status="SUCCESS",
        created_at=datetime(
            2026,
            6,
            8,
            10,
            30,
            0,
            tzinfo=pytz.UTC,
        ),
    )

    storage_dependencies = SimpleNamespace(
        allowed_users=SimpleNamespace(get_by_telegram_id=lambda telegram_id: True),
        audit_log=SimpleNamespace(list_recent=lambda limit=50: [audit_action]),
    )
    tg_bot = TelegramBot(storage_dependencies)
    tg_bot.telegram = telegram_client

    assert tg_bot.handle_message(Cmd.LAST_ACTION, telegram_id=1, username="alice") is True
    assert telegram_client.sent_messages == [
        ("📝 Last action\n\nUser: alice\nCommand: /invoice\nStatus: SUCCESS\nTime: 2026-06-08 10:30:00"),
    ]
