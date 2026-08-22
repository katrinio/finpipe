# Finpipe

Finpipe is a Telegram bot that generates salary and bank documents from a saved profile. A requested document is generated as a PDF, sent to the requesting Telegram chat, and removed from the server immediately after the delivery attempt.

![Finpipe workflow](docs/header.svg)

## What it does

- Stores company, bank-account, payment, invoice-amount, and signature data.
- Generates a Salary Invoice from the current profile and amount.
- Generates a Conversion Request for the amount extracted from the latest bank document.
- Accepts a bank PDF in Telegram and generates a filled Bank Transfer Confirmation from it.
- Sends the generated PDF directly to Telegram.
- Removes generated PDF and intermediate DOCX files after delivery, including failed delivery attempts.
- Accepts commands only from the Telegram account configured by `BOT_OWNER_TELEGRAM_ID`.

Finpipe does not connect to or send messages through an electronic-mail provider.

## Stack

- Python 3.14 and Poetry
- PostgreSQL, SQLAlchemy, and Alembic
- Telegram Bot API (polling)
- Docker Compose

## Quick start

```bash
poetry install
cp .env.dist .env
# Fill in .env
./scripts/setup_database.sh
poetry run start_bot
```

Required application variables are documented in [.env.dist](.env.dist). At minimum, configure the Telegram bot token, owner Telegram ID, signature encryption key, and database URL. Requests from every other Telegram account are rejected without creating user records.

`DATABASE_URL` is the only source of PostgreSQL host, port, database, username, and password. The PostgreSQL container derives the official image initialization settings and healthcheck connection from this URI without printing it or placing it in command arguments. For an existing volume, configure `DATABASE_URL` with credentials that the database role already accepts; changing the URI alone does not rotate an existing PostgreSQL role password.

## Telegram flow

1. Open `Profile` and download the YAML template.
2. Fill it in and upload it to the bot.
3. Upload the signature used by signed document workflows.
4. For a Salary Invoice, open `Documents` → `Invoice`, set the amount, and choose `Create invoice`.
5. For a Bank Transfer Confirmation, choose it in `Documents` and upload the source bank PDF.
6. To generate a Conversion Request for the extracted amount, choose it in `Documents` after the bank confirmation completes.

The bot sends every generated PDF to the same Telegram chat and deletes all temporary input, PDF, and intermediate DOCX files.

## Docker

```bash
docker compose up -d postgres
docker compose run --rm finpipe-bot python -m src.workflows.monitoring.backup_database
docker compose run --rm finpipe-bot alembic upgrade head
docker compose up -d --wait finpipe-bot

# Local PostgreSQL port exposure
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

Production deploy stops the bot, invokes the existing database backup workflow into the persistent project directory `./backups`, applies Alembic migrations, and waits for the new bot readiness check. No separate retention policy is applied by deploy; retention remains the responsibility of the existing daily backup infrastructure. The readiness check verifies Telegram API access and reads every active ORM table. If a migration has committed, deploy never starts the old image against the new schema.

### Database restore

Backups are plain PostgreSQL SQL dumps compressed as `./backups/finpipe_YYYY-MM-DD_HH-MM-SS.sql.gz`. List them with:

```bash
find ./backups -maxdepth 1 -name 'finpipe_*.sql.gz' -print
```

To restore, first preserve the current database separately and stop the bot. The restore command recreates the database configured by `DATABASE_URL`, then feeds the selected dump to `psql` using libpq environment inherited only by its child processes:

```bash
docker compose stop finpipe-bot
docker compose exec -T postgres python3 /usr/local/bin/finpipe-postgres-runtime --restore /backups/finpipe_YYYY-MM-DD_HH-MM-SS.sql.gz
docker compose run --rm finpipe-bot alembic current
docker compose up -d --wait finpipe-bot
```

Do not run `alembic upgrade` automatically after restoring unless the restored revision has first been checked with `alembic current` and the corresponding application version is available.

## Quality checks

```bash
poetry run ruff check .
poetry run mypy src
poetry run pytest
poetry run alembic check
```

## Documentation

| Topic | File |
|---|---|
| Development and debugging | [docs/development.md](docs/development.md) |
| Storage | [docs/storage.md](docs/storage.md) |
