"""Bootstrap для заполнения таблицы разрешённых Telegram-пользователей."""

from __future__ import annotations

from src.constants import Dir
from src.storage.database import Database, build_sqlite_url
from src.storage.repositories.allowed_user_repository import SQLAlchemyAllowedUserRepository
from src.utils.credentials import EnvVar


def main() -> None:
    database = Database(build_sqlite_url(Dir.STORAGE_DB))
    database.initialize_schema()

    repository = SQLAlchemyAllowedUserRepository(database.session)
    repository.add(
        telegram_id=int(EnvVar.get_required_env("TELEGRAM_ADMIN_ID")),
        user_name=EnvVar.get_required_env("TELEGRAM_ADMIN_USERNAME"),
    )


if __name__ == "__main__":
    main()
