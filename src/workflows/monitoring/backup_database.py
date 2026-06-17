"""Production database backup workflow for Finpipe."""

from __future__ import annotations

import gzip
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.integrations.telegram.client import TelegramClient
from src.services.monitoring.notifications import get_monitoring_chat_id
from src.utils.credentials import LOGGER, EnvVar


@dataclass(frozen=True)
class BackupConfig:
    project_dir: Path
    backup_dir: Path
    retention_days: int
    database_url: str


def load_backup_config() -> BackupConfig:
    project_dir = EnvVar.PROJECT_ROOT
    backup_dir_value = EnvVar.get_optional_env("BACKUP_DIR", str(project_dir / "backups")).strip()
    backup_dir = Path(backup_dir_value).expanduser()
    if not backup_dir.is_absolute():
        backup_dir = project_dir / backup_dir

    retention_days = int(EnvVar.get_optional_env("BACKUP_RETENTION_DAYS", "7"))
    database_url = _build_pg_dump_database_url(EnvVar.get_required_env("DATABASE_URL"))

    return BackupConfig(
        project_dir=project_dir,
        backup_dir=backup_dir,
        retention_days=retention_days,
        database_url=database_url,
    )


def run_backup(now: datetime | None = None) -> Path:
    config = load_backup_config()
    config.backup_dir.mkdir(parents=True, exist_ok=True)

    backup_name = _build_backup_filename(now or datetime.now(UTC))
    backup_path = config.backup_dir / backup_name
    tmp_path = backup_path.with_suffix(".sql")

    LOGGER.info("Starting database backup: project=%s backup_dir=%s retention_days=%s", config.project_dir, config.backup_dir, config.retention_days)

    _run_pg_dump(config=config, output_path=tmp_path)
    _gzip_file(tmp_path, backup_path)
    _ensure_non_empty(backup_path)
    _cleanup_old_backups(config.backup_dir, config.retention_days)

    size_bytes = backup_path.stat().st_size
    message = f"💾 Database backup completed\nFile: {backup_path.name}\nSize: {_format_size(size_bytes)}\nRetention: {config.retention_days} days"
    TelegramClient().send_message(get_monitoring_chat_id(), message)
    LOGGER.info("Database backup completed: file=%s size_bytes=%s", backup_path, size_bytes)
    return backup_path


def main() -> int:
    EnvVar.load_dotenv()
    try:
        run_backup()
    except Exception:
        LOGGER.exception("Database backup failed.")
        try:
            TelegramClient().send_message(get_monitoring_chat_id(), "❌ Database backup failed")
        except Exception:
            LOGGER.exception("Failed to send database backup failure notification.")
        return 1
    return 0


def _build_pg_dump_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return "postgresql://" + database_url.removeprefix("postgresql+psycopg://")
    if database_url.startswith("postgresql://"):
        return database_url
    raise RuntimeError("DATABASE_URL must use postgresql or postgresql+psycopg scheme")


def _build_backup_filename(now: datetime) -> str:
    return f"finpipe_{now.astimezone(UTC).strftime('%Y-%m-%d_%H-%M-%S')}.sql.gz"


def _run_pg_dump(config: BackupConfig, output_path: Path) -> None:
    command = ["pg_dump", f"--dbname={config.database_url}"]
    LOGGER.info("Running pg_dump for %s", config.database_url)
    with output_path.open("wb") as handle:
        completed = subprocess.run(command, stdout=handle, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace").strip() or "pg_dump failed")


def _gzip_file(source_path: Path, target_path: Path) -> None:
    with source_path.open("rb") as source, gzip.open(target_path, "wb") as destination:
        shutil.copyfileobj(source, destination)
    source_path.unlink(missing_ok=True)


def _ensure_non_empty(path: Path) -> None:
    if not path.exists() or path.stat().st_size <= 0:
        raise RuntimeError(f"Backup file is missing or empty: {path}")


def _cleanup_old_backups(backup_dir: Path, retention_days: int) -> None:
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    for path in backup_dir.glob("finpipe_*.sql.gz"):
        if datetime.fromtimestamp(path.stat().st_mtime, tz=UTC) < cutoff:
            path.unlink(missing_ok=True)
            LOGGER.info("Removed old backup: %s", path.name)


def _format_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size_bytes} B"


if __name__ == "__main__":
    raise SystemExit(main())
