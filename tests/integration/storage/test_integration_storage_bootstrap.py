from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.constants import Dir
from src.storage.bootstrap_allowed_users import bootstrap_primary_admin
from src.storage.orm import AllowedUser, Signature
from src.storage.orm.database import Database, build_sqlite_url


def test_application_startup_bootstraps_admin_and_signature_on_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_ADMIN_ID", "9001")
    monkeypatch.setenv("TELEGRAM_ADMIN_USERNAME", "primary-admin")
    source = tmp_path / "signature.png"
    source.write_bytes(b"signature-bytes")
    monkeypatch.setenv("SIGNATURE_SOURCE_PATH", str(source))
    monkeypatch.setattr(Dir, "SIGNATURE_ENC", tmp_path / "signatures" / "9001_sign.enc")

    db_path = tmp_path / "storage.sqlite3"

    bootstrap_primary_admin(db_path)

    first_admin = AllowedUser.get_by_telegram_id(9001)
    first_signature = Signature.get_active(9001)

    assert first_admin is not None
    assert first_signature is not None
    assert first_signature.signature_path.endswith("signatures/9001_sign.enc")
    assert first_signature.signature_hash == hashlib.sha256((tmp_path / "signatures" / "9001_sign.enc").read_bytes()).hexdigest()

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
    assert not source.exists()
