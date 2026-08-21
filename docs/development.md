# Development

## Environment

Copy `.env.dist` to `.env` and configure Telegram, database, monitoring, and signature-encryption values. The bot is the only application process; PostgreSQL is its only Compose dependency.

## Run locally

```bash
poetry install
./scripts/setup_database.sh
poetry run start_bot
```

## Checks

```bash
poetry run ruff check .
poetry run mypy src
poetry run pytest
poetry run alembic check
```

Generated documents are temporary delivery artifacts. The delivery workflow deletes both PDF and intermediate DOCX files after the Telegram request completes or fails.
