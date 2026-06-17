from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from src.workflows.monitoring import backup_database
from tests.fakes.fake_telegram import FakeTelegramClient


def test_build_backup_filename_uses_expected_format() -> None:
    filename = backup_database._build_backup_filename(datetime(2026, 6, 17, 5, 0, 0, tzinfo=UTC))

    assert filename == "finpipe_2026-06-17_05-00-00.sql.gz"


def test_backup_cleanup_removes_files_older_than_retention(tmp_path) -> None:
    old_file = tmp_path / "finpipe_2026-06-10_05-00-00.sql.gz"
    new_file = tmp_path / "finpipe_2026-06-17_05-00-00.sql.gz"
    old_file.write_bytes(b"old")
    new_file.write_bytes(b"new")

    old_mtime = datetime.now(UTC) - timedelta(days=10)
    new_mtime = datetime.now(UTC) - timedelta(days=1)
    old_ts = old_mtime.timestamp()
    new_ts = new_mtime.timestamp()
    old_file.touch()
    new_file.touch()
    Path(old_file).chmod(0o644)
    Path(new_file).chmod(0o644)
    import os

    os.utime(old_file, (old_ts, old_ts))
    os.utime(new_file, (new_ts, new_ts))

    backup_database._cleanup_old_backups(tmp_path, retention_days=7)

    assert not old_file.exists()
    assert new_file.exists()


def test_run_backup_sends_monitoring_message_and_creates_gz_file(monkeypatch, tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    monkeypatch.setattr(backup_database.EnvVar, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("BACKUP_DIR", str(backup_dir))
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "7")
    monkeypatch.setenv("BACKUP_POSTGRES_SERVICE", "postgres")
    monkeypatch.setenv("MONITORING_CHAT_ID", "555")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://finpipe:finpipe@postgres:5432/finpipe")

    fake_telegram = FakeTelegramClient()
    monkeypatch.setattr(backup_database, "TelegramClient", lambda: fake_telegram)

    def fake_run(command, stdout, stderr, check):
        stdout.write(b"CREATE TABLE test();\n")
        return SimpleNamespace(returncode=0, stderr=b"")

    monkeypatch.setattr(backup_database.subprocess, "run", fake_run)

    path = backup_database.run_backup(now=datetime(2026, 6, 17, 5, 0, 0, tzinfo=UTC))

    assert path.exists()
    assert path.name == "finpipe_2026-06-17_05-00-00.sql.gz"
    assert path.suffixes == [".sql", ".gz"]
    assert fake_telegram.sent_messages_with_chat_ids[-1][0] == 555
    assert fake_telegram.sent_messages_with_chat_ids[-1][1].startswith("💾 Database backup completed")
    assert "Retention: 7 days" in fake_telegram.sent_messages_with_chat_ids[-1][1]


def test_main_returns_one_and_sends_failure_notification(monkeypatch) -> None:
    fake_telegram = FakeTelegramClient()
    monkeypatch.setattr(backup_database.EnvVar, "load_dotenv", lambda: None)
    monkeypatch.setattr(backup_database, "TelegramClient", lambda: fake_telegram)
    monkeypatch.setattr(backup_database, "run_backup", lambda now=None: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setenv("MONITORING_CHAT_ID", "555")
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")

    assert backup_database.main() == 1
    assert fake_telegram.sent_messages_with_chat_ids[-1][0] == 555
    assert fake_telegram.sent_messages_with_chat_ids[-1][1] == "❌ Database backup failed"
