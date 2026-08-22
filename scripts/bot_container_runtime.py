#!/usr/bin/env python3
"""Run a Finpipe command with a Docker-network PostgreSQL address."""

from __future__ import annotations

import os
import sys
from urllib.parse import urlsplit, urlunsplit

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def container_database_url(database_url: str) -> str:
    """Translate only a host-loopback URL to the Compose PostgreSQL service."""

    parsed = urlsplit(database_url)
    if parsed.hostname not in LOOPBACK_HOSTS:
        return database_url

    userinfo, separator, _ = parsed.netloc.rpartition("@")
    if not separator:
        userinfo = ""
    netloc = f"{userinfo}@postgres:5432" if userinfo else "postgres:5432"
    return urlunsplit(parsed._replace(netloc=netloc))


def main(arguments: list[str] | None = None) -> int:
    resolved_arguments = arguments if arguments is not None else sys.argv[1:]
    if not resolved_arguments:
        print("Bot container runtime requires a command", file=sys.stderr)
        return 1

    environment = os.environ.copy()
    if database_url := environment.get("DATABASE_URL"):
        environment["DATABASE_URL"] = container_database_url(database_url)

    os.execvpe(resolved_arguments[0], resolved_arguments, environment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
