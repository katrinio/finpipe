# Development

Local setup, running, and debugging Finpipe.

---

## Prerequisites

| Tool | Purpose |
|---|---|
| Python 3.14 | Runtime |
| Poetry | Dependency management |
| PostgreSQL | Database |
| cloudflared | Gmail OAuth via local tunnel |

```bash
poetry install
cp .env.dist .env
```

Required `.env` variables:

| Variable | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token |
| `BOT_OWNER_TELEGRAM_ID` | Owner's Telegram ID |
| `SIGNATURE_ENCRYPTION_KEY` | Encryption key for signatures |
| `GMAIL_CREDENTIALS_PATH` | Path to `credentials.json` (or use `GMAIL_CLIENT_ID` + `GMAIL_CLIENT_SECRET`) |
| `DATABASE_URL` | PostgreSQL connection string |
| `EMAIL_DRY_RUN` | `true` — emails are not sent (for development and CI) |
| `EMAIL_DRY_RUN_RECIPIENT` | Email for test delivery (when `EMAIL_DRY_RUN=false`) |

---

## First run

```bash
./scripts/setup_database.sh
```

Applies Alembic migrations and creates the primary owner. Safe to run multiple times.

---

## Alembic

| Action | Command |
|---|---|
| Create migration | `poetry run alembic revision --autogenerate -m "description"` |
| Apply migrations | `poetry run alembic upgrade head` |
| Roll back one | `poetry run alembic downgrade -1` |
| Current revision | `poetry run alembic current` |
| List heads | `poetry run alembic heads` |
| Migration history | `poetry run alembic history` |
| Mark without running | `poetry run alembic stamp head` |

In practice, `revision --autogenerate` and `upgrade head` are the ones you'll use most.

---

## Telegram bot

```bash
poetry run python src/integrations/telegram/bot.py
```

The bot reads `DATABASE_URL` and other settings from `.env`.

---

## FastAPI

Needed for handling the Gmail OAuth callback.

```bash
poetry run uvicorn src.interfaces.web.app:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## Local infrastructure

A full local setup needs three processes running:

```
Google OAuth ──► Cloudflare Tunnel ──► FastAPI
                                           ▲
                                    Telegram Bot
```

| Process | Command |
|---|---|
| FastAPI | `poetry run uvicorn src.interfaces.web.app:app --host 0.0.0.0 --port 8000` |
| Telegram Bot | `poetry run python src/integrations/telegram/bot.py` |
| Cloudflare Tunnel | `./scripts/start_oauth_tunnel.sh` |

---

## Gmail OAuth (local)

```bash
./scripts/start_oauth_tunnel.sh
# or with a different port:
PORT=8080 ./scripts/start_oauth_tunnel.sh
```

The script:
- starts a Cloudflare Quick Tunnel
- builds the callback URL: `https://<tunnel-host>/oauth/gmail/callback`
- writes `GMAIL_OAUTH_CALLBACK_URL` to `.env`

Then:

1. Copy the `OAuth Redirect URI` from the script output
2. Add it in Google Cloud Console → `Authorized redirect URIs`
3. Set `GMAIL_OAUTH_CALLBACK_ENABLED=true` in `.env`
4. In Telegram: `📧 Gmail` → `🔗 Connect`

> ⚠️ The Quick Tunnel URL changes on every restart — you'll need to update the redirect URI in Google Cloud Console each time.

See [docs/oauth.md](oauth.md) for details.

---

## Tests

| Command | What it runs |
|---|---|
| `poetry run pytest -q` | All tests |
| `poetry run pytest tests/unit` | Unit tests only |
| `poetry run pytest tests/integration` | Integration tests only |
| `poetry run mypy src` | Type checking |
| `poetry run ruff check .` | Linter |

---

## Debugging

**Health check:**

```bash
curl http://localhost:8000/health
```

**Recent OAuth sessions:**

```sql
SELECT id, state, telegram_id, status, expires_at, used_at
FROM oauth_sessions
ORDER BY id DESC
LIMIT 5;
```

**Recent Gmail connections:**

```sql
SELECT id, owner_telegram_id,
       gmail_refresh_token IS NOT NULL AS has_token,
       gmail_connected_at, gmail_last_error
FROM gmail_account
ORDER BY id DESC
LIMIT 5;
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Cloudflare Error 1033` | Tunnel can't reach FastAPI — check `curl http://localhost:8000/health` |
| `redirect_uri_mismatch` | Update the redirect URI in Google Cloud Console to match the current tunnel URL |
| `OAuth callback returns 400` | Make sure the flow was started via `Connect Gmail`, not a direct URL |
| `callback flow is disabled` | Set `GMAIL_OAUTH_CALLBACK_ENABLED=true` and `GMAIL_OAUTH_CALLBACK_URL=https://...` in `.env` |

---

## Telegram UI

The bot uses a **reply keyboard** for navigation.

### Menu structure

```
/start → Main menu
├── 📄 Documents
│   ├── 🧾 Invoice
│   │   ├── 💰 Set amount
│   │   ├── 💶 Current amount
│   │   └── 📄 Generate invoice → [📤 Send to company | ✖️ Skip]
│   └── 🏦 Bank day → info screen [▶️ Run | 🏠 Home]
│       └── ▶️ Run → workflow → [📤 Reply to bank | ✖️ Skip]
├── 📧 Gmail
│   ├── 🔗 Connect / ❌ Disconnect
│   ├── 📊 Status
│   ├── 🏠 Home
│   └── 🗑 Reset history → confirmation [🗑 Yes, reset | ✖️ Cancel]
├── 👤 My profile
│   ├── 👁 View profile
│   ├── 📥 Download template / 📤 Upload profile
│   ├── ✍️ Upload signature / 🗑 Delete signature
│   └── 🏠 Home
└── 📖 Help
    ├── ❓ Getting started / ✅ Readiness
    └── 🏠 Home
```

### Button types

- **Reply keyboard** — section navigation
- **One-time reply keyboard** — single-action choices (send / skip)

### Shared button constants

`NavigationButtons.HOME` — returns to the main menu (used in all submenus).  
`NavigationButtons.SKIP` — `✖️ Skip` button (used in invoice and bank day prompts).

### Status icons

| Icon | Meaning | Where used |
|---|---|---|
| ✅ | All checks passed — ready | Operation result (`MsgIcon.success`) |
| ✔️ | Individual checklist item OK | Readiness list (`MsgIcon.status`) |
| ❌ | Operation failed | Operation result (`MsgIcon.error`) |
| ❗ | Individual checklist item failed | Readiness list (`MsgIcon.status`) |
| ➖ | Partially filled | Profile fields |

Rule: `✅`/`❌` for the outcome of an action or a set. `✔️`/`❗` for individual items within a list.

### Bank day

Tapping "🏦 Bank day" shows a readiness screen:
- ✔️/❗ Profile (company + bank details)
- ✔️/❗ Bank email search settings
- ✔️/❗ Signature
- ✔️/❗ Gmail

After tapping "▶️ Run", the workflow generates three documents and sends them to the chat. The reply to the bank goes to all original recipients (To + CC).

If the user taps `✖️ Skip` — both `ProcessedMessage` keys are removed, so the email can be processed again and the monitor will re-notify.

### ProcessedMessage sync

The `processed_messages` table is used by two systems with separate key prefixes:

| Key | Written by | Meaning |
|---|---|---|
| `{message_id}` | `fetch_bank_email_workflow` | Email was downloaded and processed by bank day |
| `notify:{telegram_id}:{message_id}` | `check_bank_email` (cron) | User already received a notification |

When bank day processes an email, both keys are written (so the monitor won't notify again). When the user skips the reply, both keys are removed (so the email can be reprocessed and the monitor will notify on the next cron run).
