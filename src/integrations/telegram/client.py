import requests

from src.utils.credentials import EnvVar


class TelegramClient:
    def __init__(self) -> None:
        self.token = EnvVar.get_required_env("TELEGRAM_BOT_TOKEN")
        self.chat_id = EnvVar.get_required_env("TELEGRAM_CHAT_ID")

    def send_message(self, text: str) -> None:
        requests.post(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            json={
                "chat_id": self.chat_id,
                "text": text,
            },
            timeout=10,
        ).raise_for_status()
