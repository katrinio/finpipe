"""Клиент Telegram Bot API для уведомлений workflow."""

from datetime import UTC, datetime
from pathlib import Path

from src.infrastructure.http.http_client import HttpClient
from src.integrations.telegram.api import TelegramApi
from src.utils import Utils
from src.utils.credentials import EnvVar


class TelegramClient:
    """Отправляет сообщения и PDF-документы в настроенный чат."""

    def __init__(self, api: TelegramApi | None = None) -> None:
        self.token = EnvVar.get_required_env("TELEGRAM_BOT_TOKEN")
        # TelegramClient остаётся публичным фасадом, а HTTP-инфраструктура живёт отдельно.
        self.api = api or TelegramApi(token=self.token, http_client=HttpClient())

    def healthcheck(self) -> None:
        """Проверяет, что токен Telegram-бота валиден."""

        payload = self.api.get_me()

        if not payload["ok"]:
            msg = "Telegram API healthcheck failed"
            raise RuntimeError(msg)

    def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None) -> None:
        """Отправляет текстовое сообщение в целевой Telegram-чат."""

        self.api.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

    def send_document(self, chat_id: int, document_path: Path) -> None:
        """Отправляет PDF-файл в Telegram как документ."""

        self.api.send_document(chat_id=chat_id, document_path=document_path)

    def get_file(self, file_id: str) -> str:
        """Возвращает file_path для файла Telegram."""

        payload = self.api.get_file(file_id=file_id)

        if not payload.get("ok"):
            msg = f"Telegram API getFile failed for file_id={file_id}"
            raise RuntimeError(msg)

        file_path = payload["result"]["file_path"]
        return str(file_path)

    def download_file(self, file_path: str) -> bytes:
        """Скачивает файл Telegram Bot API по file_path."""

        return self.api.download_file(file_path=file_path)

    def get_updates(self, offset: int | None = None) -> dict:
        """Получает входящие Telegram updates."""

        return self.api.get_updates(offset=offset)

    def send_daily_report(
        self,
        chat_id: int,
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

        self.send_message(chat_id, report_message)
