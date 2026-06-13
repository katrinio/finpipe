#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"
PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
TUNNEL_TARGET_URL="http://127.0.0.1:${PORT}"
TUNNEL_LOG="$(mktemp)"
API_LOG="$(mktemp)"

# TODO(vps): заменить локальный запуск через Cloudflare на systemd/docker-сервисы с постоянным HTTPS-доменом.

cleanup() {
  for pid in "${BOT_PID:-}" "${API_PID:-}" "${CLOUDFLARED_PID:-}"; do
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}" 2>/dev/null || true
    fi
  done
  rm -f "${TUNNEL_LOG}" "${API_LOG}"
}

trap cleanup EXIT INT TERM

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed or not found in PATH." >&2
  exit 1
fi

cd "${PROJECT_ROOT}"
touch "${ENV_FILE}"

cloudflared tunnel --url "${TUNNEL_TARGET_URL}" >"${TUNNEL_LOG}" 2>&1 &
CLOUDFLARED_PID=$!

TUNNEL_URL=""
for _ in $(seq 1 60); do
  if ! kill -0 "${CLOUDFLARED_PID}" 2>/dev/null; then
    cat "${TUNNEL_LOG}" >&2
    echo "cloudflared exited before publishing a tunnel URL." >&2
    exit 1
  fi

  TUNNEL_URL="$(sed -nE 's#.*(https://[a-zA-Z0-9.-]+\.trycloudflare\.com).*#\1#p' "${TUNNEL_LOG}" | head -n 1)"
  if [[ -n "${TUNNEL_URL}" ]]; then
    break
  fi
  sleep 1
done

if [[ -z "${TUNNEL_URL}" ]]; then
  cat "${TUNNEL_LOG}" >&2
  echo "Failed to extract Cloudflare Tunnel URL from cloudflared output." >&2
  exit 1
fi

CALLBACK_URL="${TUNNEL_URL}/oauth/gmail/callback"

python3 - "${ENV_FILE}" "${CALLBACK_URL}" <<'PY'
from pathlib import Path
import sys

env_file = Path(sys.argv[1])
callback_url = sys.argv[2]
updates = {
    "GMAIL_OAUTH_CALLBACK_ENABLED": "true",
    "GMAIL_OAUTH_CALLBACK_URL": callback_url,
}

lines = env_file.read_text().splitlines() if env_file.exists() else []
seen: set[str] = set()
for index, existing in enumerate(lines):
    if not existing or existing.startswith("#") or "=" not in existing:
        continue
    key = existing.split("=", 1)[0]
    if key in updates:
        lines[index] = f"{key}={updates[key]}"
        seen.add(key)

for key, value in updates.items():
    if key not in seen:
        lines.append(f"{key}={value}")

env_file.write_text("\n".join(lines) + "\n")
PY

export GMAIL_OAUTH_CALLBACK_ENABLED=true
export GMAIL_OAUTH_CALLBACK_URL="${CALLBACK_URL}"

echo "Tunnel URL:"
echo "${TUNNEL_URL}"
echo "OAuth Redirect URI:"
echo "${CALLBACK_URL}"
echo
echo "Paste this Redirect URI into Google Cloud Console if it changed."
echo

poetry run uvicorn src.interfaces.web.app:app --host "${HOST}" --port "${PORT}" >"${API_LOG}" 2>&1 &
API_PID=$!

for _ in $(seq 1 30); do
  if ! kill -0 "${API_PID}" 2>/dev/null; then
    cat "${API_LOG}" >&2
    echo "FastAPI exited before health check passed." >&2
    exit 1
  fi

  if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  cat "${API_LOG}" >&2
  echo "FastAPI health check failed." >&2
  exit 1
fi

echo "FastAPI:"
echo "http://127.0.0.1:${PORT}/health"
echo
echo "Starting Telegram bot..."

poetry run python src/integrations/telegram/bot.py &
BOT_PID=$!
wait "${BOT_PID}"
