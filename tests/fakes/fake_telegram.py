class FakeTelegramClient:
    def __init__(self, updates: dict | None = None, files: dict[str, bytes] | None = None) -> None:
        self.sent_messages: list[str] = []
        self._updates = updates or {"result": []}
        self._files = files or {}

    def send_message(self, text: str, reply_markup: dict | None = None) -> None:
        self.sent_messages.append(text)

    def get_updates(self, offset: int | None = None) -> dict:
        return self._updates

    def get_file(self, file_id: str) -> str:
        return file_id

    def download_file(self, file_path: str) -> bytes:
        return self._files.get(file_path, b"")

    def healthcheck(self) -> None:
        return None
