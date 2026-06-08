"""Bootstrap для заполнения таблицы разрешённых Telegram-пользователей."""

from __future__ import annotations

from src.constants import Dir
from src.storage.database import Database, build_sqlite_url
from src.storage.repositories.allowed_user_repository import SQLAlchemyAllowedUserRepository


def main() -> None:
    database = Database(build_sqlite_url(Dir.STORAGE_DB))
    database.initialize_schema()

    repository = SQLAlchemyAllowedUserRepository(database.session)
    repository.add(telegram_id=249517409, user_name="erichismyonlyfamily")


if __name__ == "__main__":
    main()
