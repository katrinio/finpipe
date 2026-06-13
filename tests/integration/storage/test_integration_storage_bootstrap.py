import hashlib
from collections.abc import Generator
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from scripts.bootstrap_allowed_users import bootstrap_primary_admin
from src.constants import Dir
from src.infrastructure.security.signature_cipher import SignatureCipher
from src.storage.migrations import run_alembic_upgrade_head
from src.storage.orm import AllowedUser, Signature, UserRole
from src.storage.orm.database import Database, build_sqlite_url
from src.utils.credentials import EnvVar
from tests.helpers.database import initialize_test_database


@pytest.fixture(autouse=True)
def signature_encryption_key(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    monkeypatch.setenv("SIGNATURE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    EnvVar.reset_dotenv_cache()
    SignatureCipher._cipher = None
    yield
    SignatureCipher._cipher = None
    EnvVar.reset_dotenv_cache()


def test_application_startup_bootstraps_admin_and_signature_on_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "9001")
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_USERNAME", "primary-admin")
    source = tmp_path / "signature.png"
    source.write_bytes(b"signature-bytes")
    monkeypatch.setenv("SIGNATURE_SOURCE_PATH", str(source))
    monkeypatch.setattr(Dir, "SIGNATURE_ENC", tmp_path / "signatures" / "9001_sign.enc")

    db_path = tmp_path / "storage.sqlite3"
    run_alembic_upgrade_head(db_path)

    bootstrap_primary_admin(db_path)

    first_admin = AllowedUser.get_by_telegram_id(9001)
    first_signature = Signature.get_active(9001)

    assert first_admin is not None
    assert first_admin.role == UserRole.OWNER
    assert first_signature is not None
    assert first_signature.signature_path.endswith("signatures/9001_sign.enc")
    assert first_signature.signature_hash == hashlib.sha256((tmp_path / "signatures" / "9001_sign.enc").read_bytes()).hexdigest()

    bootstrap_primary_admin(db_path)

    database = Database(build_sqlite_url(db_path))
    initialize_test_database(database)

    second_admin = AllowedUser.get_by_telegram_id(9001)
    second_signature = Signature.get_active(9001)

    assert second_admin is not None
    assert second_signature is not None
    assert second_admin.telegram_id == first_admin.telegram_id
    assert second_signature.id == first_signature.id
    assert len(AllowedUser.list_all()) == 1
    assert Signature.exists(9001)
    assert not source.exists()


def test_bootstrap_primary_admin_promotes_existing_owner_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "9001")
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_USERNAME", "primary-admin")
    monkeypatch.setattr(Dir, "SIGNATURE_ENC", tmp_path / "signatures" / "9001_sign.enc")

    db_path = tmp_path / "storage.sqlite3"
    run_alembic_upgrade_head(db_path)
    database = Database(build_sqlite_url(db_path))
    database.bind_models()
    AllowedUser.create(9001, "existing", UserRole.USER)

    bootstrap_primary_admin(db_path)

    admin = AllowedUser.get_by_telegram_id(9001)
    assert admin is not None
    assert admin.username == "existing"
    assert admin.role == UserRole.OWNER
