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

Fast, isolated tests — no network, no filesystem, no external services.

| Area | Examples |
|---|---|
| Business logic | Invoice generation, amount calculations |
| ORM models | Create, read, update |
| Telegram handlers | Command routing, state handling |
| Validation | Profile, bank details |

---

### integration

Tests covering multiple components together. Local PostgreSQL, filesystem, and document templates are allowed.

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
| `FakeTelegram` | `TelegramClient` |
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
| `pytest` | All tests |
| `pytest tests/unit` | Unit only |
| `pytest tests/integration` | Integration only |
| `pytest tests/external` | External only |
| `pytest -q` | Compact output |

---

## CI

CI runs only `unit` and `integration` tests — fast and deterministic.

`external` tests are not run automatically — use them for manual integration checks.

Before opening a PR: run `pytest` locally, all tests must pass.
