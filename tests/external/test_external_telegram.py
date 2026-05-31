from src.integrations.telegram.client import TelegramClient


def test_external_telegram():
    TelegramClient().send_message("Finpipe test message")
