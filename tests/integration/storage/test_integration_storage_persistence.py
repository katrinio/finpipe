from __future__ import annotations

from pathlib import Path

from src.storage.orm.database import Database, build_sqlite_url
from src.storage.orm.user.company_profile import CompanyProfile


def test_sqlite_data_survives_database_reinitialization(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "finpipe.db"

    first_database = Database(build_sqlite_url(db_path))
    first_database.initialize_schema()

    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name="Test Company",
        company_address="Belgrade",
    )

    first_profile = CompanyProfile.get_by_owner(123)
    assert first_profile is not None
    assert first_profile.company_name == "Test Company"

    second_database = Database(build_sqlite_url(db_path))
    second_database.initialize_schema()

    second_profile = CompanyProfile.get_by_owner(123)
    assert second_profile is not None
    assert second_profile.company_name == "Test Company"
    assert second_profile.company_address == "Belgrade"
    assert second_profile.id == first_profile.id
