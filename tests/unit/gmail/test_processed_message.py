import json

from src.storage import processed_messages


def test_load_processed_messages_returns_empty_set_when_file_missing(
    tmp_path, monkeypatch
) -> None:
    storage_file = tmp_path / "processed_messages.json"

    monkeypatch.setattr(
        processed_messages,
        "FILE_PATH",
        storage_file,
    )

    assert processed_messages.load_processed_messages() == set()


def test_mark_as_processed_saves_message_id(tmp_path, monkeypatch) -> None:
    storage_file = tmp_path / "processed_messages.json"

    monkeypatch.setattr(
        processed_messages,
        "FILE_PATH",
        storage_file,
    )

    processed_messages.mark_as_processed("message-123")
    assert storage_file.exists()

    with open(storage_file, encoding="utf-8") as file:
        data = json.load(file)

    assert data == {
        "processed_messages": ["message-123"],
    }


def test_is_processed_returns_true_for_saved_message(tmp_path, monkeypatch) -> None:
    storage_file = tmp_path / "processed_messages.json"

    storage_file.write_text(
        json.dumps(
            {
                "processed_messages": [
                    "message-123",
                    "message-456",
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        processed_messages,
        "FILE_PATH",
        storage_file,
    )

    assert processed_messages.is_processed("message-123") is True
    assert processed_messages.is_processed("message-999") is False
