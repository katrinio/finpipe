from __future__ import annotations

import gzip
import shutil
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from src.storage.config import DatabaseConfig
from src.storage.orm.user.company_profile import CompanyProfile
from src.workflows.monitoring import backup_database


@contextmanager
def isolated_postgres_database() -> Iterator[str]:
    source_url = make_url(DatabaseConfig.get_test_database_url())
    database_name = f"finpipe_it_{uuid4().hex}"
    admin_engine = create_engine(source_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    admin_engine.dispose()

    database_url = source_url.set(database=database_name).render_as_string(hide_password=False)
    try:
        yield database_url
    finally:
        admin_engine = create_engine(source_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as connection:
            connection.execute(
                text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = :database_name"),
                {"database_name": database_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        admin_engine.dispose()


def alembic_config(database_url: str) -> Config:
    config = Config(str(Path(__file__).resolve().parents[3] / "alembic.ini"))
    config.attributes["database_url"] = database_url
    config.attributes["skip_logging_config"] = True
    return config


def test_single_owner_migration_preserves_active_production_data() -> None:
    with isolated_postgres_database() as database_url:
        config = alembic_config(database_url)
        command.upgrade(config, "d4e5f6a7b8c9")
        engine = create_engine(database_url)
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO user_config (
                        telegram_id, onboarding_shown, invoice_amount_eur,
                        received_amount_eur, exchange_amount_eur,
                        bank_received_amount_eur, conversion_amount_eur
                    ) VALUES (123, TRUE, 1500, 1200.5, 1100.25, 1200.5, 1100.25)
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO company_profile (owner_telegram_id, company_name, company_address)
                    VALUES (123, 'Finpipe Owner', 'Belgrade')
                    """
                )
            )
            connection.execute(text("INSERT INTO allowed_users (telegram_id, username, role) VALUES (123, 'owner', 'admin')"))

        command.upgrade(config, "e8f1a2b3c4d5")

        inspector = inspect(engine)
        assert "allowed_users" not in inspector.get_table_names()
        assert {column["name"] for column in inspector.get_columns("user_config")} == {
            "telegram_id",
            "onboarding_shown",
            "invoice_amount_eur",
            "bank_received_amount_eur",
            "created_at",
            "updated_at",
        }
        with engine.connect() as connection:
            config_row = connection.execute(
                text("SELECT invoice_amount_eur, bank_received_amount_eur FROM user_config WHERE telegram_id = 123")
            ).one()
            company_name = connection.execute(text("SELECT company_name FROM company_profile WHERE owner_telegram_id = 123")).scalar_one()
        assert tuple(config_row) == (1500, 1200.5)
        assert company_name == "Finpipe Owner"
        engine.dispose()


@pytest.mark.skipif(shutil.which("pg_dump") is None or shutil.which("psql") is None, reason="PostgreSQL client tools are unavailable")
def test_pg_dump_can_be_restored_into_empty_postgres(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source_url = DatabaseConfig.get_test_database_url()
    monkeypatch.setenv("DATABASE_URL", source_url)
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path / "backups"))
    CompanyProfile.upsert(owner_telegram_id=321, company_name="Backup Owner", company_address="Belgrade")

    backup_path = backup_database.run_backup()
    assert backup_path.exists()

    with isolated_postgres_database() as restored_url:
        restore_env = backup_database._build_postgres_environment(restored_url)
        with gzip.open(backup_path, "rb") as backup_stream:
            completed = subprocess.run(
                ["psql", "--no-password", "-v", "ON_ERROR_STOP=1"],
                stdin=backup_stream,
                capture_output=True,
                check=False,
                env=restore_env,
            )
        assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")

        restored_engine = create_engine(restored_url)
        with restored_engine.connect() as connection:
            company_name = connection.execute(text("SELECT company_name FROM company_profile WHERE owner_telegram_id = 321")).scalar_one()
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        restored_engine.dispose()
        assert company_name == "Backup Owner"
        assert revision == "e8f1a2b3c4d5"
