import requests

from src.utils.credentials import EnvVar


class TelegramClient:
    def __init__(self) -> None:
        self.token = EnvVar.get_required_env("TELEGRAM_BOT_TOKEN")
        self.chat_id = EnvVar.get_required_env("TELEGRAM_CHAT_ID")

    def healthcheck(self) -> None:
        response = requests.get(
            f"https://api.telegram.org/bot{self.token}/getMe",
            timeout=10,
        )

        response.raise_for_status()
        payload = response.json()

        if not payload["ok"]:
            msg = "Telegram API healthcheck failed"
            raise RuntimeError(msg)

    def send_message(self, text: str) -> None:
        requests.post(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            json={
                "chat_id": self.chat_id,
                "text": text,
            },
            timeout=10,
        ).raise_for_status()
