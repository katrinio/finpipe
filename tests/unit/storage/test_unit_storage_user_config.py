from pathlib import Path

from src.storage.orm import UserConfig
from src.storage.orm.database import Database, build_sqlite_url
from tests.helpers.database import initialize_test_database


def test_user_config_upsert_creates_and_updates_invoice_amount(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    initialize_test_database(database)

    UserConfig.upsert(telegram_id=123, invoice_amount_eur=1500)
    created = UserConfig.get_by_owner(123)

    assert created is not None
    assert created.invoice_amount_eur == 1500

    UserConfig.upsert(telegram_id=123, invoice_amount_eur=2500)
    updated = UserConfig.get_by_owner(123)

    assert updated is not None
    assert updated.invoice_amount_eur == 2500


def test_user_config_upsert_preserves_existing_amount_when_none_is_passed(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    initialize_test_database(database)

    UserConfig.upsert(telegram_id=123, invoice_amount_eur=1500)
    UserConfig.upsert(telegram_id=123, invoice_amount_eur=None)

    config = UserConfig.get_by_owner(123)

    assert config is not None
    assert config.invoice_amount_eur == 1500


def test_user_config_upsert_defaults_exchange_amount_to_received_amount(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    initialize_test_database(database)

    UserConfig.upsert(telegram_id=123, received_amount_eur=1450.75)

    config = UserConfig.get_by_owner(123)

    assert config is not None
    assert config.received_amount_eur == 1450.75
    assert config.bank_received_amount_eur == 1450.75
    assert config.exchange_amount_eur is None


def test_user_config_upsert_preserves_explicit_exchange_amount(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    initialize_test_database(database)

    UserConfig.upsert(telegram_id=123, received_amount_eur=1450.75, exchange_amount_eur=1200.0)

    config = UserConfig.get_by_owner(123)

    assert config is not None
    assert config.received_amount_eur == 1450.75
    assert config.exchange_amount_eur == 1200.0
