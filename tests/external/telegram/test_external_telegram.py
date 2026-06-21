import os

import pytest

from src.integrations.telegram.client import TelegramClient


@pytest.mark.skipif(
    os.getenv("RUN_EXTERNAL_TELEGRAM_TESTS") != "1",
    reason="Использует реальный Telegram Bot API. Для ручной отладки: RUN_EXTERNAL_TELEGRAM_TESTS=1 pytest tests/external/",
)
def test_external_telegram_healthcheck() -> None:
    TelegramClient().healthcheck()
