from __future__ import annotations

from pathlib import Path

from src.storage.orm import AllowedUser
from src.storage.orm.database import Database, build_sqlite_url


def test_allowed_user_create_persists_user_and_marks_existence(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    AllowedUser.create(123, "alice")

    user = AllowedUser.get_by_telegram_id(123)

    assert user is not None
    assert user.telegram_id == 123
    assert user.username == "alice"
    assert user.user_name == "alice"
    assert AllowedUser.exists(123) is True


def test_allowed_user_upsert_updates_username_without_duplicate_records(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    AllowedUser.create(123, "alice")
    AllowedUser.upsert(123, "bob")

    users = AllowedUser.list_all()

    assert len(users) == 1
    assert users[0].telegram_id == 123
    assert users[0].username == "bob"
