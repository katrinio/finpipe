from src.integrations.telegram.bot import handle_message


def test_gmail_integration() -> None:
    handle_message("/status")
