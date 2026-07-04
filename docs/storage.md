# Storage

All profiles, bank details, states, and integration data are stored in PostgreSQL and survive application restarts.

---

## Connection

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/finpipe
```

---

## User data

| Table | What's stored |
|---|---|
| `company_profile` | Employer: name, address, accounting email, registration number, city, contract date |
| `bank_details` | Bank account: IBAN, BIC, account number, holder name, email, address |
| `user_config` | Settings: invoice amount, received amount, conversion amount |
| `signature` | Signature metadata + encrypted bytes (`signature_data`) |
| `gmail_account` | Gmail: encrypted refresh token, email, last error |
| `pending_bank_reply` | Pending bank reply: thread_id, subject, sender, cc, paths to 3 documents |

---

## System data

| Table | What's stored |
|---|---|
| `allowed_user` | Authorized users and their roles |
| `known_user` | Anyone who has ever opened the bot |
| `user_state_storage` | Current Telegram workflow state |
| `telegram_update` | Processed updates (prevents duplicates after restart) |
| `oauth_session` | Temporary Gmail OAuth sessions |
| `processed_message` | Processed bank emails + notification markers `notify:{tid}:{msg_id}` |
| `document_generation_history` | History of all document generation attempts |
| `audit_log` | Log of all user actions and OAuth events |
| `app_events` | System events for monitoring |

---

## Access model

Finpipe uses two separate entities for Telegram access.

### KnownUser

Anyone who has ever messaged the bot. Does not imply access.

| Field | Type |
|---|---|
| `telegram_id` | bigint |
| `username` | text |
| `first_name` | text |
| `created_at` | timestamp |
| `last_seen_at` | timestamp |

### AllowedUser

A user the owner has granted access to. The only source of permissions.

| Field | Type |
|---|---|
| `telegram_id` | bigint |
| `username` | text |
| `role` | text |
| `created_at` | timestamp |

---

## Document generation history

`document_generation_history` is a log of attempts, not a record of existing files.

| Field | Description |
|---|---|
| `document_type` | `salary_invoice` / `bank_confirmation` / `conversion_order` |
| `document_number` | Document number |
| `telegram_id` | Who triggered it |
| `status` | Success or failure |
| `error_message` | Error text (on failure) |
| `created_at` | Attempt timestamp |

Regenerating the same document is allowed. PDFs and DOCX files are not stored permanently.

---

## Security

| Data | Protection |
|---|---|
| Gmail refresh token | Encrypted via `TokenCipher` before saving |
| User signature | Encrypted via `SignatureCipher`, bytes stored in `signature_data` |
| Sensitive fields | Must not appear in logs (IBAN, tokens, email, address) |

---

## Timestamps

All timestamps are stored without microseconds:

```
YYYY-MM-DD HH:MM:SS
```

Automatic timestamps use `CURRENT_TIMESTAMP`. Timestamps set from Python are truncated to seconds before writing.

---

## Migrations

Schema is created and updated through Alembic.

```bash
# Apply all migrations
poetry run alembic upgrade head

# Create a new migration
poetry run alembic revision --autogenerate -m "description"
```

On deploy, `alembic upgrade head` runs automatically via `docker compose run --rm`.

---

## Adding a new ORM model

1. Add the model to `src/storage/orm/`
2. Export it via `__init__.py`
3. Create an Alembic migration
4. Add tests
5. Update this file if the structure changed

---

## Backup and restore

| Action | Tool |
|---|---|
| Backup | `pg_dump` |
| Restore | `pg_restore` or `psql` |

After restore, restart the application.

---

## Troubleshooting

| Symptom | What to check |
|---|---|
| Data missing after restart | `DATABASE_URL` points to the right DB; volume was not removed |
| Errors after update | Run `alembic upgrade head`; check that schema matches the code |
