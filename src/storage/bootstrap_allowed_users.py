"""Bootstrap для первичного админа и его подписи."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from src.constants import Dir
from src.infrastructure.security.signature_cipher import SignatureCipher
from src.integrations.telegram.settings import TelegramSettings
from src.storage.orm import AllowedUser, Signature
from src.storage.orm.database import Database, build_sqlite_url
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


def bootstrap_primary_admin(db_path: Path = Dir.STORAGE_DB) -> None:
    """Создаёт primary admin и, если доступна, регистрирует его подпись."""

    database = Database(build_sqlite_url(db_path))
    database.initialize_schema()

    telegram_id = TelegramSettings.owner_telegram_id()
    user_name = EnvVar.get_required_env("TELEGRAM_ADMIN_USERNAME")
    signature_source = resolve_signature_source_path()
    signature_destination = Dir.SIGNATURE_ENC.parent / f"{telegram_id}_sign.enc"

    AllowedUser.upsert(telegram_id=telegram_id, username=user_name)

    # Signature bootstrap is optional for MVP.
    # If no source file is present, admin bootstraps without a signature and the bot still starts.
    if not signature_destination.exists():
        if signature_source.exists():
            signature_destination = SignatureCipher.encrypt_file(signature_source, signature_destination)

            Signature.create(
                owner_telegram_id=telegram_id,
                signature_path=signature_destination,
                signature_hash=hashlib.sha256(signature_destination.read_bytes()).hexdigest(),
                active=True,
            )

            if signature_source.exists() and signature_source != signature_destination:
                signature_source.unlink()
        else:
            LOGGER.info("Signature source is absent, skipping signature bootstrap for Telegram user %s", telegram_id)
    else:
        Signature.create(
            owner_telegram_id=telegram_id,
            signature_path=signature_destination,
            signature_hash=hashlib.sha256(signature_destination.read_bytes()).hexdigest(),
            active=True,
        )


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
