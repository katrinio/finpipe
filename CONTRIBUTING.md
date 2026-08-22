# Contributing

Finpipe is a personal automation project, but PRs and issues are welcome.

## Before you start

- Architecture and setup — [docs/development.md](docs/development.md)
- Storage behavior — [docs/storage.md](docs/storage.md)
- Production Docker, backup, and restore workflow — [README.md](README.md#docker)

## Setup

Full instructions — [docs/development.md](docs/development.md). Short version:

```bash
poetry install
poetry run pre-commit install
```

## Before a PR

```bash
poetry run ruff check .
poetry run mypy src
poetry run alembic heads
poetry run alembic check
poetry run pytest tests
```

These checks run in CI on every PR. The test job uses PostgreSQL and enforces at least 70% source coverage; the real Telegram test remains opt-in and is skipped in CI.

## Style

- new business logic goes into `src/services/` or `src/workflows/`, not into handlers;
- user-facing strings go in the relevant `messages.py`, not hardcoded in the code;
- Telegram handlers stay thin — delegate to services and workflows;
- tests are required for new storage models and business logic.

## PR

- keep it small and focused on one thing;
- if it changes the menu structure or adds a new command — update `src/integrations/telegram/README.md` in the same PR.
