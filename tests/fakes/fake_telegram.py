class FakeTelegramClient:
    def __init__(self, updates: dict | None = None) -> None:
        self.sent_messages: list[str] = []
        self._updates = updates or {"result": []}

    def send_message(self, text: str) -> None:
        self.sent_messages.append(text)

    def get_updates(self, offset: int | None = None) -> dict:
        return self._updates

    def healthcheck(self) -> None:
        return None
