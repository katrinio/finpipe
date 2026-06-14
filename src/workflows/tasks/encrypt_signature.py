"""CLI-шаг для шифрования подписи в encrypted-артефакт."""

import argparse
import hashlib
import logging
from collections.abc import Sequence
from pathlib import Path

from src.constants import Dir
from src.infrastructure.security.signature_cipher import SignatureCipher
from src.logging_config import configure_logging
from src.storage.migrations import run_alembic_upgrade_head
from src.storage.orm import AllowedUser, Signature
from src.storage.orm.database import Database
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Создаёт CLI-парсер для шифрования подписи."""

    parser = argparse.ArgumentParser(description="Encrypt signature image into an encrypted artifact.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(EnvVar.get_optional_env("SIGNATURE_SOURCE_PATH", str(Dir.SIGNATURE_PATH))),
        help=f"Path to the source signature PNG. Defaults to {Dir.SIGNATURE_PATH}.",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=Dir.SIGNATURE_ENC,
        help=f"Path to the encrypted signature artifact. Defaults to {Dir.SIGNATURE_ENC}.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI-точка входа для шифрования подписи."""

    configure_logging()
    EnvVar.get_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        encrypt_signature_workflow(args.source, args.destination)
    except Exception:
        LOGGER.exception("Signature encryption failed")
        return 1

    return 0


def encrypt_signature_workflow(source: Path, destination: Path) -> Path:
    """Шифрует подпись, сохраняет encrypted-файл и печатает итог."""

    if not source.exists():
        msg = f"Signature source not found: {source}"
        raise FileNotFoundError(msg)

    destination = SignatureCipher.encrypt_file(source, destination)
    signature_hash = hashlib.sha256(destination.read_bytes()).hexdigest()

    run_alembic_upgrade_head()
    database = Database.from_env()
    database.bind_models()
    owner = AllowedUser.get_owner()
    if owner is None:
        msg = "Owner is not bootstrapped in storage"
        raise RuntimeError(msg)
    Signature.create(
        owner_telegram_id=owner.telegram_id,
        signature_path=destination,
        signature_hash=signature_hash,
        active=True,
    )
    # test_unit_workflows_encrypt_signature проверяет именно stdout
    print(f"Signature encrypted: {source} -> {destination} (sha256={signature_hash})")
    LOGGER.info("Signature encrypted successfully: %s -> %s", source, destination)
    return destination


if __name__ == "__main__":
    raise SystemExit(main())
