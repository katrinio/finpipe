"""Bootstrap для первичного админа и его подписи."""

import hashlib
import logging
from pathlib import Path

from src.constants import Dir
from src.infrastructure.security.signature_cipher import SignatureCipher
from src.storage.orm import AllowedUser, Signature
from src.storage.orm.database import Database
from src.storage.orm.user.allowed_user import UserRole
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


def bootstrap_primary_admin() -> None:
    """Создаёт primary admin и, если доступна, регистрирует его подпись."""

    database = Database.from_env()
    database.bind_models()

    telegram_id = int(EnvVar.get_required_env("BOT_OWNER_TELEGRAM_ID"))
    user_name = EnvVar.get_required_env("BOT_OWNER_TELEGRAM_USERNAME")
    signature_source = resolve_signature_source_path()
    signature_destination = Dir.SIGNATURE_ENC.parent / f"{telegram_id}_sign.enc"

    existing_user = AllowedUser.get_by_telegram_id(telegram_id)
    if existing_user is None:
        AllowedUser.create(telegram_id=telegram_id, username=user_name, role=UserRole.OWNER)
    elif existing_user.role != UserRole.OWNER:
        AllowedUser.upsert(
            telegram_id=telegram_id,
            username=existing_user.username or user_name,
            role=UserRole.OWNER,
        )

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
