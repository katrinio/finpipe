"""Production database backup workflow for Finpipe."""

from __future__ import annotations

import gzip
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.engine import make_url

from src.logging_config import configure_logging
from src.utils.credentials import LOGGER, EnvVar


@dataclass(frozen=True)
class BackupConfig:
    project_dir: Path
    backup_dir: Path
    database_url: str


def load_backup_config() -> BackupConfig:
    project_dir = EnvVar.PROJECT_ROOT
    backup_dir_value = EnvVar.get_optional_env("BACKUP_DIR", str(project_dir / "backups")).strip()
    backup_dir = Path(backup_dir_value).expanduser()
    if not backup_dir.is_absolute():
        backup_dir = project_dir / backup_dir

    database_url = EnvVar.get_required_env("DATABASE_URL")

    return BackupConfig(
        project_dir=project_dir,
        backup_dir=backup_dir,
        database_url=database_url,
    )


def run_backup(now: datetime | None = None) -> Path:
    config = load_backup_config()
    config.backup_dir.mkdir(parents=True, exist_ok=True)

    backup_name = _build_backup_filename(now or datetime.now(UTC))
    backup_path = config.backup_dir / backup_name
    sql_tmp_path = config.backup_dir / f".{backup_name}.sql.tmp"
    gzip_tmp_path = config.backup_dir / f".{backup_name}.tmp"

    LOGGER.info("Starting database backup: project=%s backup_dir=%s", config.project_dir, config.backup_dir)

    try:
        _run_pg_dump(config=config, output_path=sql_tmp_path)
        _gzip_file(sql_tmp_path, gzip_tmp_path)
        _ensure_non_empty(gzip_tmp_path)
        gzip_tmp_path.replace(backup_path)
    finally:
        sql_tmp_path.unlink(missing_ok=True)
        gzip_tmp_path.unlink(missing_ok=True)

    size_bytes = backup_path.stat().st_size
    LOGGER.info("Database backup completed: file=%s size_bytes=%s", backup_path, size_bytes)
    return backup_path


def main() -> int:
    configure_logging()
    EnvVar.load_dotenv()
    try:
        run_backup()
    except Exception:
        LOGGER.exception("Database backup failed.")
        return 1
    return 0


def _build_backup_filename(now: datetime) -> str:
    return f"finpipe_{now.astimezone(UTC).strftime('%Y-%m-%d_%H-%M-%S')}.sql.gz"


def _run_pg_dump(config: BackupConfig, output_path: Path) -> None:
    command = ["pg_dump", "--no-password"]
    process_env = _build_postgres_environment(config.database_url)
    LOGGER.info("Running pg_dump")
    with output_path.open("wb") as handle:
        completed = subprocess.run(command, stdout=handle, stderr=subprocess.PIPE, check=False, env=process_env)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace").strip() or "pg_dump failed")


def _build_postgres_environment(database_url: str) -> dict[str, str]:
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql" or not url.host or not url.database or not url.username:
        raise RuntimeError("DATABASE_URL must contain PostgreSQL host, database, and username")

    process_env = os.environ.copy()
    process_env.update(
        {
            "PGHOST": url.host,
            "PGPORT": str(url.port or 5432),
            "PGDATABASE": url.database,
            "PGUSER": url.username,
        }
    )
    if url.password is not None:
        process_env["PGPASSWORD"] = url.password
    else:
        process_env.pop("PGPASSWORD", None)
    return process_env


def _gzip_file(source_path: Path, target_path: Path) -> None:
    with source_path.open("rb") as source, gzip.open(target_path, "wb") as destination:
        shutil.copyfileobj(source, destination)
    source_path.unlink(missing_ok=True)


def _ensure_non_empty(path: Path) -> None:
    if not path.exists() or path.stat().st_size <= 0:
        raise RuntimeError(f"Backup file is missing or empty: {path}")


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
