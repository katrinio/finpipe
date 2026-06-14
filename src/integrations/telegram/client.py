"""Клиент Telegram Bot API для уведомлений workflow."""

from datetime import UTC, datetime
from pathlib import Path

from src.infrastructure.http.http_client import HttpClient
from src.integrations.telegram.exceptions import TelegramApiError
from src.utils import Utils
from src.utils.credentials import EnvVar


class TelegramClient:
    """Telegram Bot API клиент."""

    def __init__(self, http_client: HttpClient | None = None) -> None:
        self.token = EnvVar.get_required_env("TELEGRAM_BOT_TOKEN")
        self.http = http_client or HttpClient()
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.file_base_url = f"https://api.telegram.org/file/bot{self.token}"

    def healthcheck(self) -> None:
        """Проверяет, что токен Telegram-бота валиден."""

        payload = self.http.get(f"{self.base_url}/getMe", timeout=10).json()

        if not payload["ok"]:
            msg = "Telegram API healthcheck failed"
            raise TelegramApiError(msg)

    def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None) -> None:
        """Отправляет текстовое сообщение в целевой Telegram-чат."""

        payload: dict[str, object] = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        self.http.post(
            f"{self.base_url}/sendMessage",
            json=payload,
            timeout=10,
        )

    def send_document(self, chat_id: int, document_path: Path) -> None:
        """Отправляет PDF-файл в Telegram как документ."""

        with open(document_path, "rb") as document:
            self.http.post(
                f"{self.base_url}/sendDocument",
                data={"chat_id": chat_id},
                files={
                    "document": (
                        document_path.name,
                        document,
                        "application/pdf",
                    )
                },
                timeout=30,
            )

    def get_file(self, file_id: str) -> str:
        """Возвращает file_path для файла Telegram."""

        payload = self.http.get(
            f"{self.base_url}/getFile",
            params={"file_id": file_id},
            timeout=10,
        ).json()

        if not payload.get("ok"):
            msg = f"Telegram API getFile failed for file_id={file_id}"
            raise TelegramApiError(msg)

        file_path = payload["result"]["file_path"]
        return str(file_path)

    def download_file(self, file_path: str) -> bytes:
        """Скачивает файл Telegram Bot API по file_path."""

        return self.http.get(f"{self.file_base_url}/{file_path}", timeout=30).content

    def get_updates(self, offset: int | None = None) -> dict:
        """Получает входящие Telegram updates."""

        params = {"offset": offset} if offset is not None else None
        return self.http.get(f"{self.base_url}/getUpdates", params=params, timeout=10).json()

    def send_daily_report(
        self,
        chat_id: int,
        unit_status: str,
        integration_status: str,
        telegram_status: str,
        duration_seconds: int,
        allowed_users_count: int,
    ) -> None:
        """Отправляет итоговый отчёт по ежедневной проверке проекта."""

        report_message = (
            "🌅 Finpipe daily check-\n-\n"
            f"Unit tests: {Utils.format_status(unit_status)}\n"
            f"Integration tests: {Utils.format_status(integration_status)}\n"
            f"Telegram bot: {Utils.format_status(telegram_status)}\n"
            f"Duration: {duration_seconds}s\n\n"
            "📊 Finpipe usage\n\n"
            f"Users: {allowed_users_count}\n"
            f"Active signatures: -\n"
            f"Generated invoices: -\n"
            f"Generated bank PDFs: -\n"
            f"Google accounts connected: -\n"
            f"Errors (24h): -\n-\n"
            f"{datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"
        )

        self.send_message(chat_id, report_message)
