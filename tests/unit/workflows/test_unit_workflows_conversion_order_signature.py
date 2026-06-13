from pathlib import Path

from src.constants import Dir
from src.storage.orm.database import Database, build_sqlite_url
from src.storage.orm.user.signature import Signature
from src.workflows.tasks.generate_conversion_order import resolve_signature_for_user
from tests.helpers.database import initialize_test_database


def test_resolve_signature_for_user_prefers_active_user_signature(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    initialize_test_database(database)

    user_signature = tmp_path / "42_sign.enc"
    user_signature.write_bytes(b"encrypted-signature")
    Signature.create(owner_telegram_id=42, signature_path=user_signature)

    assert resolve_signature_for_user(42, Dir.SIGNATURE_ENC) == user_signature


def test_resolve_signature_for_user_keeps_explicit_signature_override(tmp_path: Path) -> None:
    explicit_signature = tmp_path / "custom-signature.enc"

    assert resolve_signature_for_user(42, explicit_signature) == explicit_signature


def test_resolve_signature_for_user_falls_back_to_default_when_user_signature_missing(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    initialize_test_database(database)

    assert resolve_signature_for_user(42, Dir.SIGNATURE_ENC) == Dir.SIGNATURE_ENC
