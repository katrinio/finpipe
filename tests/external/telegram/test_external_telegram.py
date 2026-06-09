import os

import pytest

from src.integrations.telegram.client import TelegramClient


@pytest.mark.skipif(
    os.getenv("RUN_EXTERNAL_TELEGRAM_TESTS") != "1",
    reason="External Telegram API test is opt-in.",
)
def test_external_telegram_healthcheck() -> None:
    TelegramClient().healthcheck()
