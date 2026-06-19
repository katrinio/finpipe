from pathlib import Path


class FakeTelegramClient:
    def __init__(self, updates: dict | None = None, files: dict[str, bytes] | None = None) -> None:
        self.sent_messages: list[str] = []
        self.sent_messages_with_chat_ids: list[tuple[int, str]] = []
        self.sent_message_payloads: list[tuple[int, str, dict | None]] = []
        self.edited_message_payloads: list[tuple[int, int, str, dict | None]] = []
        self.sent_documents: list[tuple[int, str]] = []
        self._updates = updates or {"result": []}
        self._files = files or {}
        self._edit_chat_id: int | None = None
        self._edit_message_id: int | None = None

    def set_edit_target(self, chat_id: int, message_id: int) -> None:
        self._edit_chat_id = chat_id
        self._edit_message_id = message_id

    def clear_edit_target(self) -> None:
        self._edit_chat_id = None
        self._edit_message_id = None

    def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None, parse_mode: str | None = None) -> None:
        if self._edit_message_id is not None and self._edit_chat_id == chat_id:
            self.edit_message(chat_id, self._edit_message_id, text, reply_markup, parse_mode)
            self.clear_edit_target()
            return
        self.sent_messages_with_chat_ids.append((chat_id, text))
        self.sent_message_payloads.append((chat_id, text, reply_markup))
        self.sent_messages.append(text)

    def edit_message(self, chat_id: int, message_id: int, text: str, reply_markup: dict | None = None, parse_mode: str | None = None) -> None:
        self.edited_message_payloads.append((chat_id, message_id, text, reply_markup))
        # also visible in the unified lists so existing tests don't break
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

    def answer_callback_query(self, callback_query_id: str) -> None:
        pass

    def delete_message(self, chat_id: int, message_id: int) -> None:
        pass
