# Gmail Integration

Handles Gmail OAuth, email search, attachment download, and sending replies.

For the OAuth flow and configuration: [docs/oauth.md](../../../docs/oauth.md)

---

## Structure

```
gmail/
├── auth.py                 Load credentials, refresh token, build API service
├── gmail_oauth.py          Build authorization URL, handle OAuth flow
├── oauth_callback.py       FastAPI callback endpoint (/oauth/gmail/callback)
├── oauth_token_bootstrap.py  Scopes, credentials.json loading
├── account_service.py      Connect / disconnect / status logic
├── search.py               Find bank email in Gmail
├── downloader.py           Download PDF attachments
├── sender.py               Send email via Gmail API
├── gmail_sender.py         High-level send with reply threading
├── gmail_models.py         Internal data models (BankEmail)
├── exceptions.py           Exception hierarchy
└── settings.py             Gmail-related env vars
```

---

## Auth

`get_gmail_service(telegram_id)` — builds a ready-to-use Gmail API service for a connected user.

Token resolution priority:
1. `GMAIL_CLIENT_ID` + `GMAIL_CLIENT_SECRET` from env
2. `GMAIL_CREDENTIALS_PATH` — fallback to `credentials.json`

On every call, the token is refreshed via `credentials.refresh(Request())`. On `RefreshError`, the error is written to `gmail_account.gmail_last_error` and `None` is returned.

`load_connected_account_credentials(telegram_id)` — returns `Credentials | None` without building the service. Used by the Gmail token check cron.

---

## Email search

`find_bank_email(service, owner_telegram_id)` — finds the newest bank email in Gmail for the current month.

Search config is loaded from the user's profile (`BankDetails`). Falls back to env vars for local development:

| Source | Fields |
|---|---|
| Profile | `bank_confirmation_email_sender`, `_recipient`, `_subject_contains` |
| Env fallback | `BANK_EMAIL_FROM`, `BANK_EMAIL_TO`, `BANK_EMAIL_SUBJECT` |

If neither source has all three fields — raises `RuntimeError`. The bank day handler catches this and shows the user a configuration error message.

Gmail query format:
```
subject:"..." from:"..." to:"..." after:YYYY/MM/01 has:attachment
```

---

## Exceptions

All Gmail exceptions inherit from `GmailOAuthError(RuntimeError)` or `GmailSendError(RuntimeError)`.

| Exception | When |
|---|---|
| `GmailOAuthError` | Base class for all OAuth errors |
| `GmailOAuthMissingCodeError` | OAuth callback missing `code` |
| `GmailOAuthMissingStateError` | OAuth callback missing `state` |
| `GmailOAuthProviderError` | Google returned an error instead of a code |
| `GmailOAuthInvalidStateError` | State not found in DB |
| `GmailOAuthStateNotActiveError` | State already used or expired |
| `GmailOAuthStateExpiredError` | State TTL exceeded |
| `GmailOAuthTokenExchangeError` | Token exchange failed |
| `GmailSendError` | Send failed |

`GmailOAuthError` is a subclass of `RuntimeError` — exception handlers that catch `RuntimeError` must catch `GmailOAuthError` first, or they'll match the wrong branch.

---

## Data models

`BankEmail` — a frozen dataclass with the fields needed by the bank day workflow:

| Field | Description |
|---|---|
| `subject` | Email subject |
| `sender` | From address |
| `date` | Date header |
| `message_id` | Gmail message ID |
| `thread_id` | Thread ID (used for reply threading) |
| `cc` | CC addresses from the original email |
