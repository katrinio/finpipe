from collections.abc import Callable
from types import SimpleNamespace
from typing import cast

import pytest

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.ui.buttons import NavigationButtons, ProfileButtons, SignatureButtons
from src.integrations.telegram.ui.menu.profile_menu import build_signature_menu
from src.storage.dependencies import StorageDependencies
from src.storage.orm import AllowedUser
from tests.fakes.fake_storage import FakeStorage
from tests.fakes.fake_telegram import FakeTelegramClient


def test_profile_signature_button_opens_signature_menu(
    monkeypatch: pytest.MonkeyPatch,
    fake_storage: Callable[[set[int] | None], FakeStorage],
) -> None:
    monkeypatch.setattr(
        AllowedUser,
        "get_by_telegram_id",
        classmethod(lambda cls, telegram_id: SimpleNamespace(telegram_id=telegram_id, user_name="alice")),
    )
    monkeypatch.setattr(AllowedUser, "exists", classmethod(lambda cls, telegram_id: True))

    telegram_client = FakeTelegramClient()
    tg_bot = TelegramBot(cast(StorageDependencies, fake_storage({123})), telegram=cast(TelegramClient, telegram_client))

    assert tg_bot.handle_message(ProfileButtons.SIGNATURE, telegram_id=123, username="alice") is True
    assert telegram_client.sent_message_payloads == [
        (123, ProfileButtons.SIGNATURE, build_signature_menu()),
    ]
    assert telegram_client.sent_messages == [ProfileButtons.SIGNATURE]
    assert telegram_client.sent_messages_with_chat_ids == [(123, ProfileButtons.SIGNATURE)]


def test_signature_menu_contains_signature_actions() -> None:
    assert build_signature_menu() == {
        "keyboard": [
            [
                {"text": SignatureButtons.SIGNATURE_DELETE},
                {"text": SignatureButtons.SIGNATURE_UPLOAD},
            ],
            [
                {"text": SignatureButtons.SIGNATURE_STATUS},
            ],
            [
                {"text": NavigationButtons.HOME},
            ],
        ],
        "resize_keyboard": True,
    }
