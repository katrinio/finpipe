"""Работает с Telegram Bot API поверх общего HttpClient."""

from pathlib import Path
from typing import Any, cast

from src.infrastructure.http.http_client import HttpClient


class TelegramApi:
    """Инкапсулирует endpoint'ы Telegram Bot API без общей HTTP-логики."""

    def __init__(self, token: str, http_client: HttpClient) -> None:
        self._token = token
        self._http = http_client
        self._base_url = f"https://api.telegram.org/bot{self._token}"
        self._file_base_url = f"https://api.telegram.org/file/bot{self._token}"

    def get_me(self) -> dict[str, Any]:
        """Возвращает информацию о текущем Telegram-боте."""

        response = self._http.get(f"{self._base_url}/getMe", timeout=10)
        return cast(dict[str, Any], response.json())

    def send_message(self, chat_id: int, text: str, reply_markup: dict[str, Any] | None = None) -> None:
        """Отправляет текстовое сообщение в Telegram."""

        payload: dict[str, object] = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        self._http.post(
            f"{self._base_url}/sendMessage",
            json=payload,
            timeout=10,
        )

    def send_document(self, chat_id: int, document_path: Path) -> None:
        """Отправляет документ в Telegram как файл."""

        with open(document_path, "rb") as document:
            self._http.post(
                f"{self._base_url}/sendDocument",
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

    def get_file(self, file_id: str) -> dict[str, Any]:
        """Запрашивает метаданные файла Telegram."""

        response = self._http.get(
            f"{self._base_url}/getFile",
            params={"file_id": file_id},
            timeout=10,
        )
        return cast(dict[str, Any], response.json())

    def download_file(self, file_path: str) -> bytes:
        """Скачивает файл по Telegram file_path."""

        response = self._http.get(f"{self._file_base_url}/{file_path}", timeout=30)
        return response.content

    def get_updates(self, offset: int | None = None) -> dict[str, Any]:
        """Возвращает входящие update'ы Telegram-бота."""

        params = {"offset": offset} if offset is not None else None
        response = self._http.get(f"{self._base_url}/getUpdates", params=params, timeout=10)
        return cast(dict[str, Any], response.json())
