"""Клиент Telegram Bot API для уведомлений workflow."""

from datetime import UTC, datetime
from pathlib import Path

import requests

from src.utils import Utils
from src.utils.credentials import EnvVar


class TelegramClient:
    """Отправляет сообщения и PDF-документы в настроенный чат."""

    def __init__(self) -> None:
        self.token = EnvVar.get_required_env("TELEGRAM_BOT_TOKEN")
        self.chat_id = EnvVar.get_required_env("TELEGRAM_CHAT_ID")

    def healthcheck(self) -> None:
        """Проверяет, что токен Telegram-бота валиден."""

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
        """Отправляет текстовое сообщение в целевой Telegram-чат."""

        response = requests.post(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            json={
                "chat_id": self.chat_id,
                "text": text,
            },
            timeout=10,
        )

        response.raise_for_status()

    def send_document(self, document_path: Path) -> None:
        """Отправляет PDF-файл в Telegram как документ."""

        with open(document_path, "rb") as document:
            response = requests.post(
                f"https://api.telegram.org/bot{self.token}/sendDocument",
                data={"chat_id": self.chat_id},
                files={
                    "document": (
                        document_path.name,
                        document,
                        "application/pdf",
                    )
                },
                timeout=30,
            )
        response.raise_for_status()

    def get_file(self, file_id: str) -> str:
        """Возвращает file_path для файла Telegram."""

        response = requests.get(
            f"https://api.telegram.org/bot{self.token}/getFile",
            params={"file_id": file_id},
            timeout=10,
        )

        response.raise_for_status()
        payload = response.json()

        if not payload.get("ok"):
            msg = f"Telegram API getFile failed for file_id={file_id}"
            raise RuntimeError(msg)

        file_path = payload["result"]["file_path"]
        return str(file_path)

    def download_file(self, file_path: str) -> bytes:
        """Скачивает файл Telegram Bot API по file_path."""

        response = requests.get(
            f"https://api.telegram.org/file/bot{self.token}/{file_path}",
            timeout=30,
        )

        response.raise_for_status()
        return response.content

    def get_updates(self, offset: int | None = None) -> dict:
        params = {"offset": offset} if offset is not None else None
        response = requests.get(
            f"https://api.telegram.org/bot{self.token}/getUpdates",
            params=params,
            timeout=10,
        )

        response.raise_for_status()
        return response.json()

    def send_daily_report(
        self,
        unit_status: str,
        integration_status: str,
        telegram_status: str,
        duration_seconds: int,
    ) -> None:
        """Отправляет итоговый отчёт по ежедневной проверке проекта."""

        overall_success = all(
            status == "success"
            for status in (
                unit_status,
                integration_status,
                telegram_status,
            )
        )

        icon = "✅" if overall_success else "❌"

        report_message = (
            f"{icon} Finpipe daily check\n\n"
            f"Unit tests: {Utils.format_status(unit_status)}\n"
            f"Integration tests: {Utils.format_status(integration_status)}\n"
            f"Telegram bot: {Utils.format_status(telegram_status)}\n"
            f"Duration: {duration_seconds}s\n\n"
            f"{datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"
        )

        self.send_message(report_message)
