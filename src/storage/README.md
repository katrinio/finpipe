# Storage

Handles all persistent data for Finpipe.

User settings, profiles, Telegram states, Gmail accounts, and system data are stored in PostgreSQL and survive application restarts.

For the full schema: [docs/storage.md](../../docs/storage.md)

---

## Structure

```
storage/
├── orm/                         ORM models
│   ├── user/                    User data
│   │   ├── allowed_user.py
│   │   ├── known_user.py
│   │   ├── company_profile.py
│   │   ├── bank_details.py
│   │   ├── user_config.py
│   │   ├── signature.py
│   │   └── gmail_account.py
│   └── system/                  System data
│       ├── audit_log.py
│       ├── user_state_storage.py
│       ├── telegram_update.py
│       ├── processed_message.py
│       ├── oauth_session.py
│       ├── document_generation_history.py
│       └── app_events.py
├── dependencies.py              Dependency wiring
└── bootstrap_allowed_users.py  Initial owner setup
```

---

## User models

| Model | Table | Purpose |
|---|---|---|
| `AllowedUser` | `allowed_user` | Authorized users and their roles |
| `KnownUser` | `known_user` | Anyone who has ever opened the bot |
| `CompanyProfile` | `company_profile` | Employer data |
| `BankDetails` | `bank_details` | Bank account details |
| `UserConfig` | `user_config` | Settings: invoice and conversion amounts |
| `Signature` | `signature` | Signature metadata + encrypted bytes |
| `GmailAccount` | `gmail_account` | Gmail: encrypted refresh token, email, last error |

---

## System models

| Model | Table | Purpose |
|---|---|---|
| `AuditLog` | `audit_log` | Log of all commands and OAuth events |
| `UserStateStorage` | `user_state_storage` | Current Telegram workflow state |
| `TelegramUpdate` | `telegram_update` | Processed updates (prevents duplicates) |
| `ProcessedMessage` | `processed_message` | Processed bank emails and notification markers |
| `OAuthSession` | `oauth_sessions` | Temporary Gmail OAuth sessions |
| `DocumentGenerationHistory` | `document_generation_history` | History of generation attempts |
| `AppEvent` | `app_events` | System events for monitoring |

---

## Security

| Data | Protection |
|---|---|
| Gmail refresh token | Encrypted via `TokenCipher` |
| User signature | Encrypted via `SignatureCipher` |
| Sensitive fields | Must not appear in logs |

---

## Adding a new ORM model

1. Add the file to `src/storage/orm/user/` or `src/storage/orm/system/`
2. Export it via `__init__.py`
3. Create an Alembic migration: `poetry run alembic revision --autogenerate -m "description"`
4. Add tests
5. Update [docs/storage.md](../../docs/storage.md)
