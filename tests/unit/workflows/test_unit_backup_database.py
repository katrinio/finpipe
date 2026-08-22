from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.workflows.monitoring import backup_database


def test_run_backup_creates_gz_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    monkeypatch.setattr(backup_database.EnvVar, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("BACKUP_DIR", str(backup_dir))
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "7")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://finpipe:finpipe@postgres:5432/finpipe")

    def fake_run(command: list[str], stdout: Any, stderr: Any, check: bool) -> SimpleNamespace:
        assert command == ["pg_dump", "--dbname=postgresql://finpipe:finpipe@postgres:5432/finpipe"]
        stdout.write(b"CREATE TABLE test();\n")
        return SimpleNamespace(returncode=0, stderr=b"")

    monkeypatch.setattr(backup_database.subprocess, "run", fake_run)

    path = backup_database.run_backup(now=datetime(2026, 6, 17, 5, 0, 0, tzinfo=UTC))

    assert path.exists()
    assert path.name == "finpipe_2026-06-17_05-00-00.sql.gz"
    assert path.stat().st_size > 0


def test_run_backup_fails_when_pg_dump_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    monkeypatch.setattr(backup_database.EnvVar, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("BACKUP_DIR", str(backup_dir))
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "7")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://finpipe:finpipe@postgres:5432/finpipe")

    def fake_run(command: list[str], stdout: Any, stderr: Any, check: bool) -> SimpleNamespace:
        return SimpleNamespace(returncode=1, stderr=b"pg_dump: error")

    monkeypatch.setattr(backup_database.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="pg_dump: error"):
        backup_database.run_backup(now=datetime(2026, 6, 17, 5, 0, 0, tzinfo=UTC))


def test_run_backup_fails_on_empty_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    monkeypatch.setattr(backup_database.EnvVar, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("BACKUP_DIR", str(backup_dir))
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "7")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://finpipe:finpipe@postgres:5432/finpipe")

    def fake_run(command: list[str], stdout: Any, stderr: Any, check: bool) -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stderr=b"")

    monkeypatch.setattr(backup_database.subprocess, "run", fake_run)
    monkeypatch.setattr(backup_database, "_ensure_non_empty", lambda path: (_ for _ in ()).throw(RuntimeError("empty file")))

    with pytest.raises(RuntimeError, match="empty file"):
        backup_database.run_backup(now=datetime(2026, 6, 17, 5, 0, 0, tzinfo=UTC))


def test_main_returns_one_when_backup_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(backup_database.EnvVar, "load_dotenv", lambda: None)
    monkeypatch.setattr(backup_database, "run_backup", lambda now=None: (_ for _ in ()).throw(RuntimeError("boom")))

    assert backup_database.main() == 1
