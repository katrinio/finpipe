from migrations.versions import e8f1a2b3c4d5_simplify_single_owner_architecture as migration


def test_upgrade_removes_multi_user_operational_tables_and_legacy_amounts(monkeypatch) -> None:
    dropped_tables: list[str] = []
    dropped_columns: list[tuple[str, str]] = []

    monkeypatch.setattr(migration.op, "drop_table", dropped_tables.append)
    monkeypatch.setattr(migration.op, "drop_column", lambda table, column: dropped_columns.append((table, column)))

    migration.upgrade()

    assert dropped_tables == [
        "allowed_users",
        "known_users",
        "audit_log",
        "document_generation_history",
        "app_events",
    ]
    assert dropped_columns == [
        ("bank_account", "amount"),
        ("user_config", "received_amount_eur"),
        ("user_config", "conversion_amount_eur"),
        ("user_config", "exchange_amount_eur"),
    ]
