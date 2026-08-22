#!/usr/bin/env bash
set -euo pipefail

poetry run alembic upgrade head
