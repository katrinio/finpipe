from src.integrations.telegram.client import TelegramClient


def test_external_telegram_healthcheck() -> None:
    TelegramClient().healthcheck()
