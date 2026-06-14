from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from scripts.bootstrap_allowed_users import bootstrap_primary_admin
from src.infrastructure.security.signature_cipher import SignatureCipher
from src.storage.orm import Signature
from src.storage.orm.database import Database
from src.workflows.tasks.encrypt_signature import encrypt_signature_workflow
from tests.helpers.database import build_test_database_url, initialize_test_database


def test_encrypt_signature_workflow_encrypts_source_and_prints_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("SIGNATURE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_USERNAME", "admin")
    SignatureCipher._cipher = None

    source = tmp_path / "signature.png"
    destination = tmp_path / "signature.enc"
    source.write_bytes(b"signature-bytes")

    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", build_test_database_url())
    initialize_test_database(Database(build_test_database_url(db_path)))
    bootstrap_primary_admin()

    result = encrypt_signature_workflow(source, destination)

    captured = capsys.readouterr()

    assert result == destination
    assert destination.exists()
    assert SignatureCipher.decrypt_bytes(destination) == b"signature-bytes"
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    signature = Signature.get_active(777)
    assert signature is not None
    assert signature.signature_path == str(destination)
    assert signature.signature_hash == Signature._hash_path(destination)
    assert "Signature encrypted:" in captured.out
    assert str(source) in captured.out
    assert str(destination) in captured.out
