from src.storage.orm import AllowedUser, HistoryRecord, ProcessedMessage


def test_build_storage_dependencies_returns_working_repositories(tmp_path) -> None:
    assert HistoryRecord.list_invoices() == []
    assert ProcessedMessage.list_message_ids() == []
    assert AllowedUser.list_all() == []

    HistoryRecord.add_invoice("2026-05")
    ProcessedMessage.mark_as_processed("message-123")

    assert HistoryRecord.list_invoices() == ["2026-05"]
    assert ProcessedMessage.list_message_ids() == ["message-123"]
