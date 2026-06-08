from src.storage.database import Database, build_sqlite_url
from src.storage.orm import TelegramUpdate


def test_telegram_update_storage_marks_and_checks_updates(tmp_path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    assert TelegramUpdate.is_processed(123) is False

    TelegramUpdate.mark_processed(123)

    assert TelegramUpdate.is_processed(123) is True
    assert TelegramUpdate.is_processed(456) is False


def test_telegram_update_storage_is_idempotent(tmp_path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    TelegramUpdate.mark_processed(123)
    TelegramUpdate.mark_processed(123)

    assert TelegramUpdate.is_processed(123) is True
