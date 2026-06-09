from __future__ import annotations

from pathlib import Path

import pytest

from src.storage.bootstrap_allowed_users import bootstrap_primary_admin
from src.storage.database import Database, build_sqlite_url
from src.storage.orm import AllowedUser, Signature


def test_application_startup_bootstraps_admin_and_signature_on_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_ADMIN_ID", "9001")
    monkeypatch.setenv("TELEGRAM_ADMIN_USERNAME", "primary-admin")

    db_path = tmp_path / "storage.sqlite3"

    bootstrap_primary_admin(db_path)

    first_admin = AllowedUser.get_by_telegram_id(9001)
    first_signature = Signature.get_active(9001)

    assert first_admin is not None
    assert first_signature is not None
    assert first_signature.signature_path.endswith("src/storage/signatures/signature.enc")

    bootstrap_primary_admin(db_path)

    database = Database(build_sqlite_url(db_path))
    database.initialize_schema()

    second_admin = AllowedUser.get_by_telegram_id(9001)
    second_signature = Signature.get_active(9001)

    assert second_admin is not None
    assert second_signature is not None
    assert second_admin.id == first_admin.id
    assert second_signature.id == first_signature.id
    assert len(AllowedUser.list_all()) == 1
    assert Signature.exists(9001)
