# Tests

Tests are split by isolation level and dependency on external systems.

---

## Structure

```
tests/
├── unit/            Fast, isolated tests
├── integration/     Tests covering multiple components together
├── external/        Tests against real external services
├── fixtures/        Shared pytest fixtures
├── fakes/           Test implementations of dependencies
└── resources/       Test artifacts (PDFs, DOCX files, images)
```

---

## Test levels

### unit

Fast, isolated tests with no real network or external services. Temporary filesystem paths and an isolated SQLite database are allowed.

| Area | Examples |
|---|---|
| Business logic | Invoice generation, amount calculations |
| ORM models | Create, read, update against isolated test storage |
| Telegram handlers | Command routing, state handling |
| Validation | Profile, bank details |

---

### integration

Tests covering multiple components together. A reachable PostgreSQL `TEST_DATABASE_URL`, filesystem, document templates, and local conversion tools are allowed. These tests are skipped when PostgreSQL is unavailable.

| Area | Examples |
|---|---|
| ORM + PostgreSQL | Profile import to database |
| Documents | Full PDF generation |
| Telegram workflow | End-to-end command flow |
| DOCX → PDF | LibreOffice conversion |

---

### external

Tests against real external integrations such as Telegram API. Not run in CI by default.

---

### fixtures

Shared pytest fixtures. Only put things here if they're used across multiple modules — otherwise keep them next to the test.

---

### fakes

Test implementations of external dependencies. Preferred over mocks.

| Fake | Replaces |
|---|---|
| `FakeTelegramClient` | `TelegramClient` |
| `FakeTelegramUpdateStorage` | Telegram polling checkpoint |

---

### resources

Test artifacts: PDF templates, DOCX templates, images, sample documents.

---

## Philosophy

| Principle | What it means |
|---|---|
| Unit tests are fast | No IO, no network |
| Tests are independent | Run order doesn't affect results |
| Fake > Mock | Fakes are easier to read and debug |
| One behavior per test | Don't assert multiple things in one test |
| Test is readable on its own | Clear name + clear arrange/act/assert |

---

## Naming

Format: `test_<feature>.py`

```
test_unit_invoice_generator.py
test_unit_storage_user_config.py
test_integration_profile_template_import.py
test_external_telegram.py
```

Test names describe the **behavior** being tested, not the implementation.

---

## Running tests

| Command | What it runs |
|---|---|
| `poetry run pytest` | All tests; unavailable integration and opt-in external checks are skipped |
| `poetry run pytest tests/unit` | Unit only |
| `poetry run pytest tests/integration` | Integration only; requires PostgreSQL |
| `RUN_EXTERNAL_TELEGRAM_TESTS=1 poetry run pytest tests/external` | Real Telegram API check |
| `poetry run pytest -q` | Compact output |

---

## CI

CI invokes the complete `tests` tree with PostgreSQL and coverage enabled. The external Telegram test is collected but skipped because CI does not set `RUN_EXTERNAL_TELEGRAM_TESTS=1`.

Before opening a PR, run `poetry run pytest` locally; every test that is enabled by the available services and explicit opt-in flags must pass.
