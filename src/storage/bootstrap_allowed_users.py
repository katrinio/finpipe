"""Bootstrap для заполнения таблицы разрешённых Telegram-пользователей."""

from __future__ import annotations

from src.constants import Dir
from src.storage.database import Database, build_sqlite_url
from src.storage.orm import AllowedUser
from src.utils.credentials import EnvVar


def main() -> None:
    database = Database(build_sqlite_url(Dir.STORAGE_DB))
    database.initialize_schema()

    AllowedUser.add(
        telegram_id=int(EnvVar.get_required_env("TELEGRAM_ADMIN_ID")),
        user_name=EnvVar.get_required_env("TELEGRAM_ADMIN_USERNAME"),
    )


if __name__ == "__main__":
    main()
