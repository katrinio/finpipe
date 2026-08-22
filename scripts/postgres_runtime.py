#!/usr/bin/env python3
"""Derive PostgreSQL container runtime settings from Finpipe DATABASE_URL."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


def connection_environment() -> dict[str, str]:
    """Return libpq settings parsed from DATABASE_URL without logging secrets."""

    database_url = os.getenv("DATABASE_URL", "")
    parsed = urlsplit(database_url)
    if parsed.scheme not in {"postgresql", "postgresql+psycopg"}:
        raise RuntimeError("DATABASE_URL must use a PostgreSQL scheme")
    if not parsed.hostname or not parsed.username or not parsed.path.removeprefix("/"):
        raise RuntimeError("DATABASE_URL must include host, username, and database")

    environment = os.environ.copy()
    environment.update(
        {
            "PGHOST": parsed.hostname,
            "PGPORT": str(parsed.port or 5432),
            "PGDATABASE": unquote(parsed.path.removeprefix("/")),
            "PGUSER": unquote(parsed.username),
        }
    )
    if parsed.password is not None:
        environment["PGPASSWORD"] = unquote(parsed.password)
    else:
        environment.pop("PGPASSWORD", None)
    return environment


def restore_backup(backup_path: Path) -> int:
    """Recreate the configured database and restore a compressed SQL dump."""

    if not backup_path.is_file() or backup_path.suffixes[-2:] != [".sql", ".gz"]:
        raise RuntimeError("Backup must be an existing .sql.gz file")

    environment = connection_environment()
    database_name = environment["PGDATABASE"]
    maintenance_environment = environment | {"PGDATABASE": "postgres"}
    drop_process = subprocess.run(
        ["dropdb", "--force", "--if-exists", database_name],
        check=False,
        env=maintenance_environment,
    )
    if drop_process.returncode != 0:
        return drop_process.returncode
    create_process = subprocess.run(
        ["createdb", database_name],
        check=False,
        env=maintenance_environment,
    )
    if create_process.returncode != 0:
        return create_process.returncode

    gzip_process = subprocess.Popen(["gzip", "-dc", str(backup_path)], stdout=subprocess.PIPE)
    assert gzip_process.stdout is not None
    psql_process = subprocess.run(
        ["psql", "--no-password", "-v", "ON_ERROR_STOP=1"],
        stdin=gzip_process.stdout,
        check=False,
        env=environment,
    )
    gzip_process.stdout.close()
    gzip_returncode = gzip_process.wait()
    return psql_process.returncode or gzip_returncode


def run_postgres_entrypoint(arguments: list[str]) -> None:
    environment = connection_environment()
    # The upstream image requires three initialization settings. They are
    # transiently derived here and are never external Finpipe configuration.
    for suffix, libpq_name in (("DB", "PGDATABASE"), ("USER", "PGUSER"), ("PASSWORD", "PGPASSWORD")):
        setting_name = f"POSTGRES_{suffix}"
        if value := environment.get(libpq_name):
            os.environ[setting_name] = value
        else:
            os.environ.pop(setting_name, None)
    os.execv("/usr/local/bin/docker-entrypoint.sh", ["docker-entrypoint.sh", *arguments])


def main(arguments: list[str] | None = None) -> int:
    resolved_arguments = arguments if arguments is not None else sys.argv[1:]
    try:
        if len(resolved_arguments) == 2 and resolved_arguments[0] == "--restore":
            return restore_backup(Path(resolved_arguments[1]))
        run_postgres_entrypoint(resolved_arguments)
    except Exception as error:
        print(f"PostgreSQL runtime configuration failed: {type(error).__name__}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
