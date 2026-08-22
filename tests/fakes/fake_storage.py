class FakeTelegramUpdateStorage:
    def __init__(self) -> None:
        self.processed: list[int] = []

    def get_last_processed_update_id(self) -> int | None:
        return 10

    def mark_processed(self, update_id: int) -> None:
        self.processed.append(update_id)
