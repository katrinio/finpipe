# Development

## Environment

Copy `.env.dist` to `.env` and configure the Telegram bot token, owner Telegram ID, database, and signature-encryption key. The bot is the only application process; PostgreSQL is its only Compose dependency.

## Run locally

```bash
poetry install
cp .env.dist .env
# Fill in the secrets and use localhost:5433 in DATABASE_URL
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d postgres
./scripts/setup_database.sh
poetry run start_bot
```

The distributed `DATABASE_URL` uses the Compose service address `postgres:5432`. Direct host commands cannot resolve that address, so local host-based development must use the exposed `localhost:5433` endpoint. `setup_database.sh` applies Alembic migrations; it does not start PostgreSQL.

## Checks

```bash
poetry run ruff check .
poetry run mypy src
poetry run pytest
poetry run alembic check
```

Generated documents are temporary delivery artifacts. The delivery workflow deletes both PDF and intermediate DOCX files after the Telegram request completes or fails.

Unit tests fall back to an isolated temporary SQLite database when `TEST_DATABASE_URL` is unavailable. Integration tests require a reachable PostgreSQL `TEST_DATABASE_URL` and are skipped otherwise. The real Telegram check is also skipped unless `RUN_EXTERNAL_TELEGRAM_TESTS=1` is set explicitly.

The root `Dockerfile` has two targets: `production` for the deployed bot and `ci` for quality jobs with development dependencies. `Dockerfile.postgres` remains separate because it extends PostgreSQL rather than the Python application image.
