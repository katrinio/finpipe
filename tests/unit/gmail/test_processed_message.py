from sqlalchemy import func, select

from src.storage import processed_messages
from src.storage.database import Database, build_sqlite_url
from src.storage.models import ProcessedMessage


def test_load_processed_messages_returns_empty_set_when_file_missing(tmp_path, monkeypatch) -> None:
    storage_file = tmp_path / "processed_messages.json"
    database_path = tmp_path / "storage.sqlite3"

    monkeypatch.setattr(processed_messages, "FILE_PATH", storage_file)
    monkeypatch.setattr(processed_messages, "DB_PATH", database_path)

    assert processed_messages.load_processed_messages() == set()


def test_mark_as_processed_saves_message_id(tmp_path, monkeypatch) -> None:
    storage_file = tmp_path / "processed_messages.json"
    database_path = tmp_path / "storage.sqlite3"

    monkeypatch.setattr(processed_messages, "FILE_PATH", storage_file)
    monkeypatch.setattr(processed_messages, "DB_PATH", database_path)

    processed_messages.mark_as_processed("message-123")

    database = Database(build_sqlite_url(database_path))
    with database.session() as session:
        rows = session.scalars(select(ProcessedMessage.message_id).order_by(ProcessedMessage.message_id)).all()

    assert rows == ["message-123"]


def test_is_processed_returns_true_for_saved_message(tmp_path, monkeypatch) -> None:
    storage_file = tmp_path / "processed_messages.json"
    storage_file.write_text(
        '{"processed_messages": ["message-123", "message-456"]}',
        encoding="utf-8",
    )
    database_path = tmp_path / "storage.sqlite3"

    monkeypatch.setattr(processed_messages, "FILE_PATH", storage_file)
    monkeypatch.setattr(processed_messages, "DB_PATH", database_path)

    assert processed_messages.is_processed("message-123") is True
    assert processed_messages.is_processed("message-999") is False


def test_is_processed_list_clean(tmp_path, monkeypatch) -> None:
    storage_file = tmp_path / "processed_messages.json"
    database_path = tmp_path / "storage.sqlite3"

    monkeypatch.setattr(processed_messages, "FILE_PATH", storage_file)
    monkeypatch.setattr(processed_messages, "DB_PATH", database_path)

    processed_messages.mark_as_processed("message-123")
    processed_messages.clear_processed_history()

    database = Database(build_sqlite_url(database_path))
    with database.session() as session:
        count = session.scalar(select(func.count()).select_from(ProcessedMessage))

    assert count == 0
