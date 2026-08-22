import sqlalchemy as sa

from migrations.versions import d4e5f6a7b8c9_remove_email_integration as migration


def test_downgrade_restores_pending_reply_cc_constraints(monkeypatch) -> None:
    created_tables: dict[str, tuple[sa.Column, ...]] = {}

    monkeypatch.setattr(migration.op, "add_column", lambda *args, **kwargs: None)
    monkeypatch.setattr(migration.op, "create_index", lambda *args, **kwargs: None)
    monkeypatch.setattr(migration.op, "f", lambda name: name)
    monkeypatch.setattr(
        migration.op,
        "create_table",
        lambda table_name, *columns, **kwargs: created_tables.setdefault(table_name, columns),
    )

    migration.downgrade()

    pending_columns = {column.name: column for column in created_tables["pending_bank_reply"]}
    cc_column = pending_columns["cc"]
    assert cc_column.nullable is False
    assert cc_column.server_default is not None
    assert cc_column.server_default.arg == ""
