from pathlib import Path

from src.storage.orm import UserConfig
from src.storage.orm.database import Database, build_sqlite_url


def test_user_config_upsert_creates_and_updates_invoice_amount(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    UserConfig.upsert(telegram_id=123, invoice_amount=1500)
    created = UserConfig.get_by_owner(123)

    assert created is not None
    assert created.invoice_amount == 1500

    UserConfig.upsert(telegram_id=123, invoice_amount=2500)
    updated = UserConfig.get_by_owner(123)

    assert updated is not None
    assert updated.invoice_amount == 2500


def test_user_config_upsert_preserves_existing_amount_when_none_is_passed(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    UserConfig.upsert(telegram_id=123, invoice_amount=1500)
    UserConfig.upsert(telegram_id=123, invoice_amount=None)

    config = UserConfig.get_by_owner(123)

    assert config is not None
    assert config.invoice_amount == 1500
