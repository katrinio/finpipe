# Contributing

Finpipe is a personal automation project, but PRs and issues are welcome.

## Before you start

- Architecture and setup — [docs/development.md](docs/development.md)
- Storage schema — [docs/storage.md](docs/storage.md)
- Monitoring — [docs/monitoring.md](docs/monitoring.md)

## Setup

Full instructions — [docs/development.md](docs/development.md). Short version:

```bash
poetry install
poetry run pre-commit install
```

## Before a PR

```bash
poetry run ruff check .
poetry run mypy .
poetry run pytest tests/unit tests/integration
```

All three run in CI on every PR — a red CI won't get merged.

## Style

- new business logic goes into `src/services/` or `src/workflows/`, not into handlers;
- user-facing strings go in the relevant `messages.py`, not hardcoded in the code;
- Telegram handlers stay thin — delegate to services and workflows;
- tests are required for new storage models and business logic.

## PR

- keep it small and focused on one thing;
- if it changes the menu structure or adds a new command — update `src/integrations/telegram/README.md` in the same PR.
