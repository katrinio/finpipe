#!/usr/bin/env bash

set -euo pipefail

required_variables=(
  DATABASE_URL
  SIGNATURE_ENCRYPTION_KEY
  TELEGRAM_BOT_TOKEN
)

missing=0
for variable_name in "${required_variables[@]}"; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "ERROR: ${variable_name} is missing"
    missing=1
  fi
done

if (( missing != 0 )); then
  exit 1
fi

case "$DATABASE_URL" in
  postgresql://* | postgresql+psycopg://*) ;;
  *)
    echo "ERROR: DATABASE_URL must use a PostgreSQL scheme"
    exit 1
    ;;
esac

echo "Production configuration: OK"
