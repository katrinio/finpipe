from datetime import UTC, datetime

import requests

from src.utils import Utils
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

    def send_daily_report(
        self,
        unit_status: str,
        integration_status: str,
        telegram_status: str,
        duration_seconds: int,
    ) -> None:

        overall_success = all(
            status == "success"
            for status in (
                unit_status,
                integration_status,
                telegram_status,
            )
        )

        icon = "✅" if overall_success else "❌"

        message = (
            f"{icon} Finpipe daily check\n\n"
            f"Unit tests: {Utils.format_status(unit_status)}\n"
            f"Integration tests: {Utils.format_status(integration_status)}\n"
            f"Telegram bot: {Utils.format_status(telegram_status)}\n"
            f"Duration: {duration_seconds}s\n\n"
            f"{datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"
        )

        self.send_message(message)
