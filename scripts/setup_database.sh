#!/usr/bin/env bash
set -euo pipefail

poetry run alembic upgrade head
poetry run python scripts/bootstrap_allowed_users.py
