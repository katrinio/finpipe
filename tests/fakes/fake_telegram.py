from pathlib import Path


class FakeTelegramClient:
    def __init__(self, updates: dict | None = None, files: dict[str, bytes] | None = None) -> None:
        self.sent_messages: list[str] = []
        self.sent_messages_with_chat_ids: list[tuple[int, str]] = []
        self.sent_message_payloads: list[tuple[int, str, dict | None]] = []
        self.sent_documents: list[tuple[int, str]] = []
        self._updates = updates or {"result": []}
        self._files = files or {}

    def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None) -> None:
        self.sent_messages_with_chat_ids.append((chat_id, text))
        self.sent_message_payloads.append((chat_id, text, reply_markup))
        self.sent_messages.append(text)

    def get_updates(self, offset: int | None = None) -> dict:
        return self._updates

    def get_file(self, file_id: str) -> str:
        return file_id

    def download_file(self, file_path: str) -> bytes:
        return self._files.get(file_path, b"")

    def send_document(self, chat_id: int, document_path: Path) -> None:
        self.sent_documents.append((chat_id, str(document_path)))

    def healthcheck(self) -> None:
        return None
