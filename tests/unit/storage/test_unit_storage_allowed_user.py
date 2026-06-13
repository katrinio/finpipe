from pathlib import Path

from src.storage.orm import AllowedUser, UserRole
from src.storage.orm.database import Database, build_sqlite_url
from tests.helpers.database import initialize_test_database


def test_allowed_user_create_persists_user_and_marks_existence(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    initialize_test_database(database)

    AllowedUser.create(123, "alice")

    user = AllowedUser.get_by_telegram_id(123)

    assert user is not None
    assert user.telegram_id == 123
    assert user.username == "alice"
    assert user.user_name == "alice"
    assert user.role == UserRole.USER
    assert AllowedUser.exists(123) is True


def test_allowed_user_upsert_updates_username_without_duplicate_records(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    initialize_test_database(database)

    AllowedUser.create(123, "alice")
    AllowedUser.upsert(123, "bob")

    users = AllowedUser.list_all()

    assert len(users) == 1
    assert users[0].telegram_id == 123
    assert users[0].username == "bob"


def test_allowed_user_role_helpers_detect_owner_and_admin(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    initialize_test_database(database)

    AllowedUser.create(1, "owner", UserRole.OWNER)
    AllowedUser.create(2, "user", UserRole.USER)
    AllowedUser.create(3, "admin", UserRole.ADMIN)

    assert AllowedUser.is_owner(1) is True
    assert AllowedUser.is_admin(1) is True
    assert AllowedUser.is_owner(2) is False
    assert AllowedUser.is_admin(2) is False
    assert AllowedUser.is_owner(3) is False
    assert AllowedUser.is_admin(3) is True
