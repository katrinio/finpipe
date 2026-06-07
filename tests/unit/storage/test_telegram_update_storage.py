from src.storage.database import Database, build_sqlite_url
from src.storage.telegram_update_storage import TelegramUpdateStorage


def test_telegram_update_storage_marks_and_checks_updates(tmp_path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    storage = TelegramUpdateStorage(database.session)

    assert storage.is_processed(123) is False

    storage.mark_processed(123)

    assert storage.is_processed(123) is True
    assert storage.is_processed(456) is False


def test_telegram_update_storage_is_idempotent(tmp_path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    storage = TelegramUpdateStorage(database.session)

    storage.mark_processed(123)
    storage.mark_processed(123)

    assert storage.is_processed(123) is True
