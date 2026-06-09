"""Bootstrap для первичного админа и его подписи."""

from __future__ import annotations

from pathlib import Path

from src.constants import Dir
from src.storage.database import Database, build_sqlite_url
from src.storage.orm import AllowedUser, Signature
from src.utils.credentials import EnvVar


def bootstrap_primary_admin(db_path: Path = Dir.STORAGE_DB) -> None:
    """Создаёт primary admin и регистрирует его активную подпись."""

    database = Database(build_sqlite_url(db_path))
    database.initialize_schema()

    telegram_id = int(EnvVar.get_required_env("TELEGRAM_ADMIN_ID"))
    user_name = EnvVar.get_required_env("TELEGRAM_ADMIN_USERNAME")

    AllowedUser.add(
        telegram_id=telegram_id,
        user_name=user_name,
    )
    Signature.create(
        owner_telegram_id=telegram_id,
        signature_path=Dir.SIGNATURE_ENC,
        active=True,
    )


def main() -> None:
    bootstrap_primary_admin()


if __name__ == "__main__":
    main()
