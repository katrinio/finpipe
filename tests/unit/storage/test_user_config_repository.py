from datetime import UTC, datetime

from src.storage.database import Database, build_sqlite_url
from src.storage.orm import UserConfig


def test_user_config_repository_get_by_telegram_id(tmp_path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    with database.session() as session:
        session.add(
            UserConfig(
                telegram_id=777,
                user_name="alice",
                account_holder="Alice",
                account_holder_email="alice@example.com",
                account_holder_address="Address",
                bank_name="Bank",
                account_number="123",
                iban="IBAN",
                bic="BIC",
                company_name="Company",
                company_address="Company Address",
                service_agreement_date=datetime(2026, 1, 1, tzinfo=UTC),
                created_at=datetime(2026, 1, 2, tzinfo=UTC),
            )
        )
        session.commit()

    user = UserConfig.get_by_telegram_id(777)

    assert user is not None
    assert user.telegram_id == 777
    assert user.user_name == "alice"
    assert UserConfig.get_by_telegram_id(123) is None
