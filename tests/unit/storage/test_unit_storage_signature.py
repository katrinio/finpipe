from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.constants import Dir
from src.storage.bootstrap_allowed_users import bootstrap_primary_admin
from src.storage.orm import AllowedUser, Signature
from src.storage.orm.database import Database, build_sqlite_url


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
    assert first_signature.signature_hash == hashlib.sha256(first_path.read_bytes()).hexdigest()
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
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
    monkeypatch.setenv("TELEGRAM_ADMIN_USERNAME", "admin")
    source = tmp_path / "signature.png"
    source.write_bytes(b"signature-bytes")
    monkeypatch.setenv("SIGNATURE_SOURCE_PATH", str(source))
    monkeypatch.setattr(Dir, "SIGNATURE_ENC", tmp_path / "signatures" / "777_sign.enc")

    bootstrap_primary_admin(tmp_path / "storage.sqlite3")

    admin = AllowedUser.get_by_telegram_id(777)
    signature = Signature.get_active(777)

    assert admin is not None
    assert admin.user_name == "admin"
    assert signature is not None
    assert signature.owner_telegram_id == 777
    assert signature.signature_path == str(tmp_path / "signatures" / "777_sign.enc")
    assert signature.signature_hash == hashlib.sha256((tmp_path / "signatures" / "777_sign.enc").read_bytes()).hexdigest()
    assert not source.exists()
    assert (tmp_path / "signatures" / "777_sign.enc").exists()


def test_bootstrap_primary_admin_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
    monkeypatch.setenv("TELEGRAM_ADMIN_USERNAME", "admin")
    source = tmp_path / "signature.png"
    source.write_bytes(b"signature-bytes")
    monkeypatch.setenv("SIGNATURE_SOURCE_PATH", str(source))
    monkeypatch.setattr(Dir, "SIGNATURE_ENC", tmp_path / "signatures" / "777_sign.enc")

    db_path = tmp_path / "storage.sqlite3"
    bootstrap_primary_admin(db_path)
    first_signature = Signature.get_by_owner(777)

    bootstrap_primary_admin(db_path)
    second_signature = Signature.get_by_owner(777)

    assert first_signature is not None
    assert second_signature is not None
    assert first_signature.id == second_signature.id
    assert first_signature.signature_hash == second_signature.signature_hash
    assert len(AllowedUser.list_all()) == 1
    assert not source.exists()


def test_signature_delete_removes_db_row_and_file(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    signature_path = tmp_path / "777_sign.enc"
    signature_path.write_bytes(b"encrypted-signature")

    Signature.create(
        owner_telegram_id=777,
        signature_path=signature_path,
        signature_hash=hashlib.sha256(signature_path.read_bytes()).hexdigest(),
    )

    assert signature_path.exists()
    assert Signature.exists(777)

    Signature.delete(777)

    assert not signature_path.exists()
    assert not Signature.exists(777)
