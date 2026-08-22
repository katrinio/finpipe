from pathlib import Path

from sqlalchemy import inspect

from src.storage.orm.base import BaseModel
from src.storage.orm.database import Database
from src.storage.orm.user.company_profile import CompanyProfile
from tests.helpers.database import build_test_database_url, initialize_test_database


def test_database_data_survives_reinitialization(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "postgres.db"

    first_database = Database(build_test_database_url(db_path))
    initialize_test_database(first_database)

    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name="Test Company",
        company_address="Belgrade",
    )

    first_profile = CompanyProfile.get_by_owner(123)
    assert first_profile is not None
    assert first_profile.company_name == "Test Company"

    second_database = Database(build_test_database_url(db_path))
    initialize_test_database(second_database)

    second_profile = CompanyProfile.get_by_owner(123)
    assert second_profile is not None
    assert second_profile.company_name == "Test Company"
    assert second_profile.company_address == "Belgrade"
    assert second_profile.id == first_profile.id


def test_database_schema_matches_orm_models(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "postgres.db"

    database = Database(build_test_database_url(db_path))
    initialize_test_database(database)

    inspector = inspect(database.engine)
    for table in BaseModel.metadata.sorted_tables:
        columns = {column["name"] for column in inspector.get_columns(table.name)}
        model_columns = {column.name for column in table.columns}

        assert columns == model_columns, table.name
