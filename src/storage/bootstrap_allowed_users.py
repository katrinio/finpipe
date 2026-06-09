"""Bootstrap для первичного админа и его подписи."""

from __future__ import annotations

import hashlib
from pathlib import Path

from src.constants import Dir
from src.infrastructure.security.signature_cipher import SignatureCipher
from src.storage.database import Database, build_sqlite_url
from src.storage.orm import AllowedUser, Signature
from src.utils.credentials import EnvVar


def bootstrap_primary_admin(db_path: Path = Dir.STORAGE_DB) -> None:
    """Создаёт primary admin и регистрирует его активную подпись."""

    database = Database(build_sqlite_url(db_path))
    database.initialize_schema()

    telegram_id = int(EnvVar.get_required_env("TELEGRAM_ADMIN_ID"))
    user_name = EnvVar.get_required_env("TELEGRAM_ADMIN_USERNAME")
    signature_source = resolve_signature_source_path()
    signature_destination = Dir.SIGNATURE_ENC.parent / f"{telegram_id}_sign.enc"

    AllowedUser.add(
        telegram_id=telegram_id,
        user_name=user_name,
    )

    if not signature_destination.exists():
        if not signature_source.exists():
            msg = f"Signature source not found: {signature_source}"
            raise FileNotFoundError(msg)

        signature_destination = SignatureCipher.encrypt_file(signature_source, signature_destination)

    Signature.create(
        owner_telegram_id=telegram_id,
        signature_path=signature_destination,
        signature_hash=hashlib.sha256(signature_destination.read_bytes()).hexdigest(),
        active=True,
    )

    if signature_source.exists() and signature_source != signature_destination:
        signature_source.unlink()


def resolve_signature_source_path() -> Path:
    """Возвращает путь к исходной подписи из env или стандартного шаблона."""

    signature_path = Path(EnvVar.get_optional_env("SIGNATURE_SOURCE_PATH", str(Dir.SIGNATURE_PATH))).expanduser()
    if not signature_path.is_absolute():
        return EnvVar.PROJECT_ROOT / signature_path
    return signature_path


def main() -> None:
    bootstrap_primary_admin()


if __name__ == "__main__":
    main()
