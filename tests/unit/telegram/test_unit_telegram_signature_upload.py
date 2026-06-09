from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import cast

import pytest

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.buttons import SignatureButtons
from src.integrations.telegram.ui.messages import BotInfo
from src.services.signing.exceptions import InvalidSignatureFormatError
from src.storage.dependencies import StorageDependencies
from src.storage.orm import AllowedUser
from src.storage.orm.telegram_update import TelegramUpdate
from tests.fakes.fake_storage import FakeStorage, FakeTelegramUpdateStorage
from tests.fakes.fake_telegram import FakeTelegramClient


def test_upload_signature_sets_waiting_state(
    monkeypatch: pytest.MonkeyPatch,
    fake_storage: Callable[[set[int] | None], FakeStorage],
    fake_update_storage: FakeTelegramUpdateStorage,
) -> None:
    monkeypatch.setattr(
        AllowedUser,
        "get_by_telegram_id",
        classmethod(lambda cls, telegram_id: SimpleNamespace(telegram_id=telegram_id, user_name="alice")),
    )

    tg_bot = TelegramBot(cast(StorageDependencies, fake_storage({123})))
    telegram_client = FakeTelegramClient()
    tg_bot.telegram = cast(TelegramClient, telegram_client)
    tg_bot.update_storage = cast(type[TelegramUpdate], fake_update_storage)

    assert tg_bot.handle_message(SignatureButtons.SIGNATURE_UPLOAD, telegram_id=123, username="alice") is True
    assert tg_bot.handlers.get_user_state(123) == UserState.WAITING_SIGNATURE_UPLOAD
    assert telegram_client.sent_messages == [
        BotInfo.SIGNATURE_REQUIREMENTS,
    ]


def test_successful_signature_upload_clears_state(
    monkeypatch: pytest.MonkeyPatch,
    fake_storage: Callable[[set[int] | None], FakeStorage],
    fake_update_storage: FakeTelegramUpdateStorage,
) -> None:
    monkeypatch.setattr(
        AllowedUser,
        "get_by_telegram_id",
        classmethod(lambda cls, telegram_id: SimpleNamespace(telegram_id=telegram_id, user_name="alice")),
    )

    tg_bot = TelegramBot(cast(StorageDependencies, fake_storage({123})))
    telegram_client = FakeTelegramClient(
        files={
            "signature-file-id": b"png-bytes",
        }
    )
    tg_bot.telegram = cast(TelegramClient, telegram_client)
    tg_bot.update_storage = cast(type[TelegramUpdate], fake_update_storage)

    monkeypatch.setattr("src.integrations.telegram.handlers.SignatureService.upload", lambda **kwargs: None)

    tg_bot.handle_message(SignatureButtons.SIGNATURE_UPLOAD, telegram_id=123, username="alice")
    tg_bot.process_update(
        {
            "update_id": 42,
            "message": {
                "document": {
                    "file_id": "signature-file-id",
                    "file_name": "signature.png",
                    "file_size": 9,
                },
                "from": {"id": 123, "username": "alice"},
            },
        }
    )

    assert tg_bot.handlers.get_user_state(123) is None
    assert telegram_client.sent_messages == [
        BotInfo.SIGNATURE_REQUIREMENTS,
        BotInfo.SIGNATURE_UPDATED,
    ]
    assert fake_update_storage.processed == [42]


def test_invalid_file_keeps_state(
    monkeypatch: pytest.MonkeyPatch,
    fake_storage: Callable[[set[int] | None], FakeStorage],
    fake_update_storage: FakeTelegramUpdateStorage,
) -> None:
    monkeypatch.setattr(
        AllowedUser,
        "get_by_telegram_id",
        classmethod(lambda cls, telegram_id: SimpleNamespace(telegram_id=telegram_id, user_name="alice")),
    )

    tg_bot = TelegramBot(cast(StorageDependencies, fake_storage({123})))
    telegram_client = FakeTelegramClient(
        files={
            "signature-file-id": b"jpeg-bytes",
        }
    )
    tg_bot.telegram = cast(TelegramClient, telegram_client)
    tg_bot.update_storage = cast(type[TelegramUpdate], fake_update_storage)

    def raise_invalid(**kwargs: object) -> None:
        raise InvalidSignatureFormatError("invalid signature")

    monkeypatch.setattr("src.integrations.telegram.handlers.SignatureService.upload", raise_invalid)

    tg_bot.handle_message(SignatureButtons.SIGNATURE_UPLOAD, telegram_id=123, username="alice")
    tg_bot.process_update(
        {
            "update_id": 43,
            "message": {
                "document": {
                    "file_id": "signature-file-id",
                    "file_name": "signature.jpg",
                    "file_size": 9,
                },
                "from": {"id": 123, "username": "alice"},
            },
        }
    )

    assert tg_bot.handlers.get_user_state(123) == UserState.WAITING_SIGNATURE_UPLOAD
    assert telegram_client.sent_messages[0] == BotInfo.SIGNATURE_REQUIREMENTS
    assert fake_update_storage.processed == [43]
