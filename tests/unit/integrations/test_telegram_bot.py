from types import SimpleNamespace

from src.integrations.telegram import bot
from src.integrations.telegram.commands import BotInfo, Cmd


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


class FakeTelegramUpdateStorage:
    def __init__(self) -> None:
        self.processed: list[int] = []

    def get_last_processed_update_id(self) -> int | None:
        return 10

    def mark_processed(self, update_id: int) -> None:
        self.processed.append(update_id)


def test_poll_denies_unauthorized_user(monkeypatch, caplog) -> None:
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

    monkeypatch.setattr(bot, "TelegramClient", lambda: telegram_client)
    monkeypatch.setattr(bot, "build_storage_dependencies", lambda _db_path: FakeStorage(set()))
    monkeypatch.setattr(bot, "build_telegram_update_storage", lambda _db_path: update_storage)

    caplog.clear()
    bot.poll()

    assert "Access denied for Telegram user 999 (@intruder)" in caplog.text
    assert telegram_client.sent_messages == ["⛔ Access denied"]
    assert update_storage.processed == []


def test_poll_processes_authorized_user_and_whoami(monkeypatch) -> None:
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

    monkeypatch.setattr(bot, "TelegramClient", lambda: telegram_client)
    monkeypatch.setattr(bot, "build_storage_dependencies", lambda _db_path: FakeStorage({123}))
    monkeypatch.setattr(bot, "build_telegram_update_storage", lambda _db_path: update_storage)

    bot.poll()

    assert telegram_client.sent_messages == [
        f"{BotInfo.WHOAMI_PREFIX}\ntelegram_id: 123\nusername: alice",
    ]
    assert update_storage.processed == [11]
