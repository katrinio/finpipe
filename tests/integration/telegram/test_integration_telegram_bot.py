from datetime import UTC, datetime
from types import SimpleNamespace

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.commands import BotInfo, Cmd
from src.storage.orm import AllowedUser
from src.storage.orm.audit_log import AuditLog


class TestTelegramBot:
    def test_poll_denies_unauthorized_user(
        self,
        caplog,
        fake_telegram_client,
        fake_storage,
        fake_update_storage,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(AllowedUser, "get_by_telegram_id", classmethod(lambda cls, telegram_id: None))

        tg_bot = TelegramBot(fake_storage(set()))
        tg_bot.telegram = fake_telegram_client(
            {
                "result": [
                    {
                        "update_id": 11,
                        "message": {
                            "text": Cmd.WHOAMI,
                            "from": {"id": 999, "username": "intruder"},
                        },
                    }
                ]
            }
        )
        tg_bot.update_storage = fake_update_storage

        caplog.clear()
        tg_bot.poll()

        assert "Access denied for Telegram user 999 (@intruder)" in caplog.text
        assert tg_bot.telegram.sent_messages == [BotInfo.ACCESS_DENIED]
        assert tg_bot.update_storage.processed == []

    def test_poll_processes_authorized_user_and_whoami(self, fake_telegram_client, fake_storage, fake_update_storage, monkeypatch) -> None:
        monkeypatch.setattr(
            AllowedUser,
            "get_by_telegram_id",
            classmethod(lambda cls, telegram_id: SimpleNamespace(telegram_id=telegram_id, user_name="alice")),
        )

        tg_bot = TelegramBot(fake_storage({123}))
        tg_bot.telegram = fake_telegram_client(
            {
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
        )
        tg_bot.update_storage = fake_update_storage

        tg_bot.poll()

        assert tg_bot.telegram.sent_messages == BotInfo.WHOAMI_PREFIX
        assert tg_bot.update_storage.processed == [11]

    def test_handle_message_last_action_uses_storage_audit_log(self, fake_telegram_client) -> None:
        telegram_client = fake_telegram_client()
        audit_action = AuditLog(
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
                tzinfo=UTC,
            ),
        )

        tg_bot = TelegramBot(
            SimpleNamespace(
                allowed_users=AllowedUser(get_by_telegram_id=lambda telegram_id: True),
                audit_log=SimpleNamespace(
                    create=lambda *args, **kwargs: None,
                    list_recent=lambda limit=50: [audit_action],
                ),
            )
        )
        tg_bot.telegram = telegram_client

        assert tg_bot.handle_message(Cmd.LAST_ACTION, telegram_id=1, username="alice") is True
        assert telegram_client.sent_messages == [
            ("📝 Last action\n\nUser: alice\nCommand: /invoice\nStatus: SUCCESS\nTime: 2026-06-08 10:30:00"),
        ]
