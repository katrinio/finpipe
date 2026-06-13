#!/usr/bin/env bash

poetry run alembic upgrade head
poetry run python scripts/bootstrap_allowed_users.py