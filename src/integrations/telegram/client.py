"""Клиент Telegram Bot API для уведомлений workflow."""

from datetime import UTC, datetime
from pathlib import Path

from src.infrastructure.http.http_client import HttpClient
from src.integrations.telegram.exceptions import TelegramApiError
from src.utils.credentials import EnvVar


class TelegramClient:
    """Telegram Bot API клиент."""

    def __init__(self, http_client: HttpClient | None = None) -> None:
        self.token = EnvVar.get_required_env("TELEGRAM_BOT_TOKEN")
        self.http = http_client or HttpClient()
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.file_base_url = f"https://api.telegram.org/file/bot{self.token}"
        self._edit_chat_id: int | None = None
        self._edit_message_id: int | None = None

    def healthcheck(self) -> None:
        """Проверяет, что токен Telegram-бота валиден."""

        payload = self.http.get(f"{self.base_url}/getMe", timeout=10).json()

        if not payload["ok"]:
            msg = "Telegram API healthcheck failed"
            raise TelegramApiError(msg)

    def set_edit_target(self, chat_id: int, message_id: int) -> None:
        """Указывает сообщение, которое будет отредактировано следующим send_message."""
        self._edit_chat_id = chat_id
        self._edit_message_id = message_id

    def clear_edit_target(self) -> None:
        self._edit_chat_id = None
        self._edit_message_id = None

    def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None, parse_mode: str | None = None) -> None:
        """Отправляет текстовое сообщение; если задан edit target для этого чата — редактирует существующее."""

        if self._edit_message_id is not None and self._edit_chat_id == chat_id:
            self.edit_message(chat_id, self._edit_message_id, text, reply_markup, parse_mode)
            self.clear_edit_target()
            return

        payload: dict[str, object] = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        if parse_mode is not None:
            payload["parse_mode"] = parse_mode

        self.http.post(
            f"{self.base_url}/sendMessage",
            json=payload,
            timeout=10,
        )

    def edit_message(self, chat_id: int, message_id: int, text: str, reply_markup: dict | None = None, parse_mode: str | None = None) -> None:
        """Редактирует текст существующего сообщения."""

        payload: dict[str, object] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        if parse_mode is not None:
            payload["parse_mode"] = parse_mode

        self.http.post(
            f"{self.base_url}/editMessageText",
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

    def answer_callback_query(self, callback_query_id: str) -> None:
        """Снимает индикатор загрузки с инлайн-кнопки после её нажатия."""

        self.http.post(
            f"{self.base_url}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id},
            timeout=10,
        )

    def delete_message(self, chat_id: int, message_id: int) -> None:
        """Удаляет сообщение из чата."""

        self.http.post(
            f"{self.base_url}/deleteMessage",
            json={"chat_id": chat_id, "message_id": message_id},
            timeout=10,
        )

    def get_updates(self, offset: int | None = None) -> dict:
        """Получает входящие Telegram updates."""

        params = {"offset": offset} if offset is not None else None
        return self.http.get(f"{self.base_url}/getUpdates", params=params, timeout=10).json()

    def send_daily_report(
        self,
        chat_id: int,
        duration_seconds: int,
        allowed_users_count: int,
        active_signatures_count: int,
        generated_invoice_count: int,
        generated_bank_pdf: int,
        google_account_connected_count: int,
    ) -> None:
        """Отправляет итоговый отчёт по ежедневной проверке проекта."""

        report_message = (
            "💅 Finpipe daily check\n\n"
            f"Duration: {duration_seconds}s\n"
            "n/a\n"
            "_\n\n"
            "📊 Finpipe usage\n\n"
            f"Users: {allowed_users_count}\n"
            f"Active signatures: {active_signatures_count}\n"
            f"Generated invoices: {generated_invoice_count}\n"
            f"Generated bank PDFs: {generated_bank_pdf}\n"
            f"Google accounts connected: {google_account_connected_count}\n"
            f"Errors (24h): n/a\n"
            "_\n\n"
            f"Duration: {duration_seconds}s\n"
            f"{datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"
        )

        self.send_message(chat_id, report_message)
