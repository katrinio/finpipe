# Finpipe

If you're a sole proprietor who fills in the same bank documents every month — this is for you.

Finpipe is a Telegram bot that handles the paperwork around salary payments. When the bank sends a notification, the bot finds it in Gmail, extracts the amount, fills in three signed documents, and sends them to your chat. You can run the whole thing from your phone.

![](docs/header.svg)

---

## What it does

### Bank day

One command covers the full payment cycle:

1. Finds the bank's email in Gmail
2. Extracts the amount from the PDF attachment
3. Generates Bank Confirmation, Conversion Order, and Salary Invoice — all signed
4. Sends the documents to Telegram
5. Offers to reply to the bank with the documents attached

No laptop needed.

### Documents

| Document | Description |
|---|---|
| Salary Invoice | Payment invoice with profile data and signature |
| Bank Confirmation | Signed confirmation for the bank |
| Conversion Order | Signed currency conversion request |

### Gmail

- OAuth authorization
- Searches incoming bank emails
- Sends replies with attachments via Gmail API
- Notifies you in chat if the token expires and reconnection is needed

### Telegram

- Manage company profile and bank details
- Upload and store your signature (encrypted at rest)
- Generate documents from chat
- Monitoring chat for critical alerts

---

## Stack

- Python 3.14, Poetry
- PostgreSQL + SQLAlchemy + Alembic
- Telegram Bot API (polling)
- Gmail API (OAuth 2.0)
- Docker Compose

---

## Quick start

```bash
poetry install
cp .env.dist .env
# fill in .env
./scripts/setup_database.sh
poetry run python src/integrations/telegram/bot.py
```

For Gmail OAuth (local development):

```bash
./scripts/start_local_oauth_stack.sh
```

---

## Docker

```bash
# Main stack
docker compose up -d

# Local (with exposed ports)
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d

# Monitoring stack
docker compose -f monitoring.compose.yml up -d
```

---

## Docs

| Topic | File |
|---|---|
| Development & debugging | [docs/development.md](docs/development.md) |
| Gmail OAuth | [docs/oauth.md](docs/oauth.md) |
| Storage | [docs/storage.md](docs/storage.md) |
| Monitoring | [docs/monitoring.md](docs/monitoring.md) |
