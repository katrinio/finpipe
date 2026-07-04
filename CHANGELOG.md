# Changelog

## v1.0.0 — 2026-06-21

First stable release.

### Core workflows

- **Bank day** — full cycle: find bank email in Gmail → extract amount → generate Bank Confirmation, Conversion Order, and Salary Invoice → send documents to Telegram → reply to the bank with attachments (To + CC, subject Re: original)
- **Salary Invoice** — generated from profile, sent to the company's accounting email
- **Bank email monitoring** — cron every 5 minutes (days 2–6 of each month), Telegram notification on new email

### Telegram UI

- Reply keyboard for navigation, one-time keyboard for in-flow actions
- Info screen before bank day with readiness status (✔️ / ❗)
- Confirmation before destructive actions (Gmail history reset)
- Full profile view with automatic display after template upload
- "✅ Readiness" screen — quick check of all dependencies

### Profile

- YAML template with company data, bank details, and email search config
- `company_email` field — accounting email for invoice delivery
- Digital signature — encrypted, embedded in PDF automatically

### Gmail

- OAuth 2.0 authorization
- CC from the original bank email is preserved in the reply
- Two-level email status system: `delivered` (notified) / `processed` (handled by bank day)

### Monitoring chat

- `/health` — Telegram API, database, last activity timestamp
- `/events`, `/errors`, `/stats` — event log
- `/logs [N]` — last lines from the Docker container
- `/help` — command list
- Notifications only on WARNING and ERROR — no noise from INFO

### Infrastructure

- Docker Compose, PostgreSQL, Alembic migrations
- Auto-start via `docker compose up -d`
- Token and signature encryption via Fernet
