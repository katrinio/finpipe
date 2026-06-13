#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"
PORT="${PORT:-8000}"
TUNNEL_TARGET_URL="http://127.0.0.1:${PORT}"
LOG_FILE="$(mktemp)"

cleanup() {
  if [[ -n "${CLOUDFLARED_PID:-}" ]] && kill -0 "${CLOUDFLARED_PID}" 2>/dev/null; then
    kill "${CLOUDFLARED_PID}" 2>/dev/null || true
  fi
  rm -f "${LOG_FILE}"
}

trap cleanup EXIT INT TERM

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed or not found in PATH." >&2
  exit 1
fi

touch "${ENV_FILE}"

cloudflared tunnel --url "${TUNNEL_TARGET_URL}" >"${LOG_FILE}" 2>&1 &
CLOUDFLARED_PID=$!

TUNNEL_URL=""
for _ in $(seq 1 60); do
  if ! kill -0 "${CLOUDFLARED_PID}" 2>/dev/null; then
    cat "${LOG_FILE}" >&2
    echo "cloudflared exited before publishing a tunnel URL." >&2
    exit 1
  fi

  TUNNEL_URL="$(sed -nE 's#.*(https://[a-zA-Z0-9.-]+\.trycloudflare\.com).*#\1#p' "${LOG_FILE}" | head -n 1)"
  if [[ -n "${TUNNEL_URL}" ]]; then
    break
  fi
  sleep 1
done

if [[ -z "${TUNNEL_URL}" ]]; then
  cat "${LOG_FILE}" >&2
  echo "Failed to extract Cloudflare Tunnel URL from cloudflared output." >&2
  exit 1
fi

CALLBACK_URL="${TUNNEL_URL}/oauth/gmail/callback"

python3 - "${ENV_FILE}" "${CALLBACK_URL}" <<'PY'
from pathlib import Path
import sys

env_file = Path(sys.argv[1])
callback_url = sys.argv[2]
line = f"GMAIL_OAUTH_CALLBACK_URL={callback_url}"

lines = env_file.read_text().splitlines() if env_file.exists() else []
updated = False
for index, existing in enumerate(lines):
    if existing.startswith("GMAIL_OAUTH_CALLBACK_URL="):
        lines[index] = line
        updated = True
        break
if not updated:
    lines.append(line)

env_file.write_text("\n".join(lines) + "\n")
PY

echo "Tunnel URL:"
echo "${TUNNEL_URL}"
echo "OAuth Redirect URI:"
echo "${CALLBACK_URL}"
echo
echo "Updated ${ENV_FILE}"
echo "Press Ctrl+C to stop the tunnel."

wait "${CLOUDFLARED_PID}"
