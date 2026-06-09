from __future__ import annotations

from pathlib import Path

import pytest

from src.constants import Dir
from src.storage.bootstrap_allowed_users import bootstrap_primary_admin
from src.storage.database import Database, build_sqlite_url
from src.storage.orm import AllowedUser, Signature


def test_signature_create_persists_and_reuses_owner(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    first_path = tmp_path / "signature-v1.png"
    second_path = tmp_path / "signature-v2.png"

    first_path.write_bytes(b"signature-v1")
    second_path.write_bytes(b"signature-v2")

    Signature.create(owner_telegram_id=123, signature_path=first_path)
    first_signature = Signature.get_active(123)

    assert first_signature is not None
    assert first_signature.signature_path == str(first_path)
    assert Signature.exists(123)

    Signature.create(owner_telegram_id=123, signature_path=second_path)
    second_signature = Signature.get_active(123)

    assert second_signature is not None
    assert second_signature.id == first_signature.id
    assert second_signature.signature_path == str(second_path)
    assert second_signature.active is True


def test_bootstrap_primary_admin_creates_admin_and_active_signature(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_ADMIN_ID", "777")
    monkeypatch.setenv("TELEGRAM_ADMIN_USERNAME", "admin")

    bootstrap_primary_admin(tmp_path / "storage.sqlite3")

    admin = AllowedUser.get_by_telegram_id(777)
    signature = Signature.get_active(777)

    assert admin is not None
    assert admin.user_name == "admin"
    assert signature is not None
    assert signature.owner_telegram_id == 777
    assert signature.signature_path == str(Dir.SIGNATURE_ENC)


def test_bootstrap_primary_admin_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_ADMIN_ID", "777")
    monkeypatch.setenv("TELEGRAM_ADMIN_USERNAME", "admin")

    db_path = tmp_path / "storage.sqlite3"
    bootstrap_primary_admin(db_path)
    first_signature = Signature.get_by_owner(777)

    bootstrap_primary_admin(db_path)
    second_signature = Signature.get_by_owner(777)

    assert first_signature is not None
    assert second_signature is not None
    assert first_signature.id == second_signature.id
    assert len(AllowedUser.list_all()) == 1
