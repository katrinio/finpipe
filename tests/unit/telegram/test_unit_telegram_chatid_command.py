from collections.abc import Callable

from src.integrations.telegram.ui.buttons.system import SystemButtons

from src.integrations.telegram.handlers.command_router import CommandRouter
from src.storage.orm import AllowedUser
from src.storage.orm.system.audit_log import AuditLog
from tests.fakes.fake_telegram import FakeTelegramClient


def _build_router(telegram: FakeTelegramClient) -> CommandRouter:
    return CommandRouter(telegram=telegram, audit_log=AuditLog)


def test_chatid_is_available_to_owner(
    fake_telegram_client: Callable[..., FakeTelegramClient],
    monkeypatch,
) -> None:
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_USERNAME", "owner")
    AllowedUser.create(777, "owner")

    telegram = fake_telegram_client()
    router = _build_router(telegram)

    assert router.handle_message(SystemButtons.CHATID, telegram_id=777, username="owner") is True
    assert telegram.sent_messages_with_chat_ids[-1] == (777, "Chat ID: 777")


def test_chatid_is_hidden_from_non_owner(
    fake_telegram_client: Callable[..., FakeTelegramClient],
    monkeypatch,
) -> None:
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_USERNAME", "owner")
    AllowedUser.create(123, "alice")

    telegram = fake_telegram_client()
    router = _build_router(telegram)

    assert router.handle_message(SystemButtons.CHATID, telegram_id=123, username="alice") is False
    assert telegram.sent_messages[-1] == "⛔ У вас пока нет доступа к Finpipe.\nНажмите «Кто я» и отправьте свой Telegram ID владельцу бота."
