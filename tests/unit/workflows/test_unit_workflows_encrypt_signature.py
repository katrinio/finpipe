from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from src.constants import Dir
from src.infrastructure.security.signature_cipher import SignatureCipher
from src.storage.bootstrap_allowed_users import bootstrap_primary_admin
from src.storage.orm import Signature
from src.storage.orm.database import Database, build_sqlite_url
from src.workflows.tasks.encrypt_signature import encrypt_signature_workflow


def test_encrypt_signature_workflow_encrypts_source_and_prints_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("SIGNATURE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_USERNAME", "admin")
    SignatureCipher._cipher = None
    monkeypatch.setattr(Dir, "STORAGE_DB", tmp_path / "storage.sqlite3")

    source = tmp_path / "signature.png"
    destination = tmp_path / "signature.enc"
    source.write_bytes(b"signature-bytes")

    bootstrap_primary_admin(tmp_path / "storage.sqlite3")

    result = encrypt_signature_workflow(source, destination)

    captured = capsys.readouterr()

    assert result == destination
    assert destination.exists()
    assert SignatureCipher.decrypt_bytes(destination) == b"signature-bytes"
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    signature = Signature.get_active(777)
    assert signature is not None
    assert signature.signature_path == str(destination)
    assert signature.signature_hash == Signature._hash_path(destination)
    assert "Signature encrypted:" in captured.out
    assert str(source) in captured.out
    assert str(destination) in captured.out
