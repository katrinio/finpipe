from pathlib import Path

from src.services.known_user_service import KnownUserService
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import KnownUser


def test_known_user_registered_on_first_interaction(tmp_path: Path) -> None:
    build_storage_dependencies(tmp_path / "storage.sqlite3")

    KnownUserService.register_interaction(
        telegram_id=123,
        username="alice",
        first_name="Alice",
    )

    known_user = KnownUser.get_by_telegram_id(123)
    assert known_user is not None
    assert known_user.username == "alice"
    assert known_user.first_name == "Alice"


def test_known_user_updates_username_on_repeat_interaction(tmp_path: Path) -> None:
    build_storage_dependencies(tmp_path / "storage.sqlite3")
    KnownUserService.register_interaction(
        telegram_id=123,
        username="alice",
        first_name="Alice",
    )

    KnownUserService.register_interaction(
        telegram_id=123,
        username="alice_new",
        first_name="Alice",
    )

    known_user = KnownUser.get_by_telegram_id(123)
    assert known_user is not None
    assert known_user.username == "alice_new"
