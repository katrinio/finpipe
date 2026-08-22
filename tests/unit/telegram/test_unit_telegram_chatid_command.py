from src.integrations.telegram.buttons.system import SystemButtons
from src.integrations.telegram.handlers.command_router import CommandRouter
from tests.fakes.fake_telegram import FakeTelegramClient


def _build_router(telegram: FakeTelegramClient) -> CommandRouter:
    return CommandRouter(telegram=telegram)


def test_chatid_command_returns_current_chat_id() -> None:
    telegram = FakeTelegramClient()
    router = _build_router(telegram)

    assert router.handle_message(SystemButtons.CHATID, telegram_id=777, username="owner") is True
    assert telegram.sent_messages_with_chat_ids[-1] == (777, "Chat ID: 777")
