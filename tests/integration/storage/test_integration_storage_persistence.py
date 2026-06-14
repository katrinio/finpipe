from pathlib import Path

from sqlalchemy import inspect

from src.storage.orm import DocumentGenerationHistory
from src.storage.orm.base import BaseModel
from src.storage.orm.database import Database
from src.storage.orm.system.document_generation_history import DocumentGenerationStatus, DocumentType
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


def test_alembic_schema_supports_document_generation_history(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "postgres.db"
    database = Database(build_test_database_url(db_path))
    table_name = DocumentGenerationHistory.__tablename__

    initialize_test_database(database)

    columns = {column["name"] for column in inspect(database.engine).get_columns(table_name)}

    assert columns == {"id", "document_type", "document_number", "telegram_id", "status", "error_message", "created_at"}

    DocumentGenerationHistory.add_attempt(
        document_type=DocumentType.SALARY_INVOICE,
        document_number="2026-05",
        telegram_id=123,
        status=DocumentGenerationStatus.SUCCESS,
    )

    last_attempt = DocumentGenerationHistory.get_last_attempt(DocumentType.SALARY_INVOICE, "2026-05")
    assert last_attempt is not None
    assert last_attempt.document_number == "2026-05"
    assert last_attempt.document_type == DocumentType.SALARY_INVOICE
    assert last_attempt.status == DocumentGenerationStatus.SUCCESS
