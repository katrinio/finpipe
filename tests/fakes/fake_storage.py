from types import SimpleNamespace


class FakeUserConfigRepository:
    def __init__(self, allowed_ids: set[int]) -> None:
        self.allowed_ids = allowed_ids

    def get_by_telegram_id(self, telegram_id: int):
        if telegram_id in self.allowed_ids:
            return SimpleNamespace(
                telegram_id=telegram_id,
                user_name="alice",
            )

        return None


class FakeStorage:
    def __init__(self, allowed_ids: set[int]) -> None:
        self.allowed_users = FakeUserConfigRepository(allowed_ids)

        self.audit_log = SimpleNamespace(
            list_recent=lambda limit=50: [],
            add=lambda *args, **kwargs: None,
        )


class FakeTelegramUpdateStorage:
    def __init__(self) -> None:
        self.processed: list[int] = []

    def get_last_processed_update_id(self) -> int | None:
        return 10

    def mark_processed(self, update_id: int) -> None:
        self.processed.append(update_id)
