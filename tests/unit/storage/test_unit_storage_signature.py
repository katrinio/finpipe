import hashlib
from collections.abc import Generator
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from src.infrastructure.security.signature_cipher import SignatureCipher
from src.storage.orm import Signature
from src.storage.orm.database import Database
from src.utils.credentials import EnvVar
from tests.helpers.database import build_test_database_url, initialize_test_database


@pytest.fixture(autouse=True)
def signature_encryption_key(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    monkeypatch.setenv("SIGNATURE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    EnvVar.reset_dotenv_cache()
    SignatureCipher._cipher = None
    yield
    SignatureCipher._cipher = None
    EnvVar.reset_dotenv_cache()


def test_signature_create_persists_and_reuses_owner(tmp_path: Path) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)

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


def test_signature_delete_removes_db_row_and_file(tmp_path: Path) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)

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


def test_resolve_workflow_signature_path_recovers_legacy_path_when_user_file_exists(tmp_path: Path) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)

    legacy_path = tmp_path / "signatures" / "signature.enc"
    fallback_path = tmp_path / "signatures" / "249517409_sign.enc"
    fallback_path.parent.mkdir(parents=True, exist_ok=True)
    source = tmp_path / "signature.png"
    source.write_bytes(b"signature-bytes")
    SignatureCipher.encrypt_file(source, fallback_path)

    Signature.create(owner_telegram_id=249517409, signature_path=legacy_path, signature_hash="hash")

    resolved = Signature.resolve_workflow_signature_path(249517409)

    assert resolved == fallback_path
    assert Signature.get_active(249517409).signature_path == str(fallback_path)
