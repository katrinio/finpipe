from src.storage.dependencies import build_storage_dependencies


def test_build_storage_dependencies_returns_working_repositories(tmp_path) -> None:
    storage = build_storage_dependencies(db_path=tmp_path / "storage.sqlite3")

    assert storage.invoice_history.list_invoices() == []
    assert storage.processed_messages.list_message_ids() == []
    assert storage.user_config.get_by_telegram_id(123) is None

    storage.invoice_history.add_invoice("2026-05")
    storage.processed_messages.mark_as_processed("message-123")

    assert storage.invoice_history.list_invoices() == ["2026-05"]
    assert storage.processed_messages.list_message_ids() == ["message-123"]
