# Workflows

Workflows are high-level user scenarios that combine several tasks into a single end-to-end process.

---

## Workflows

### `generate_invoice_and_send`

Generates a Salary Invoice and sends it to Telegram, then asks whether to email it to the company.

| Step | Action |
|---|---|
| 1 | Generate Salary Invoice for the current period |
| 2 | Create PDF and DOCX |
| 3 | Record attempt in `document_generation_history` |
| 4 | Send PDF to Telegram |
| 5 | Delete DOCX; PDF stays until the user decides |
| 6a | "Send to company": `send_invoice_email` → email → delete PDF |
| 6b | "Skip": `discard_invoice_pdf` → delete PDF |

**Email env variables:**

| Variable | Purpose |
|---|---|
| `EMAIL_DRY_RUN` | `true` — email is not sent, only logged |
| `EMAIL_DRY_RUN_RECIPIENT` | Overrides the recipient address (when `false`) |

---

### `process_bank_request`

The main bank day workflow — runs on cron.

| Step | Action |
|---|---|
| 1 | Find new bank email, download PDF attachment |
| 2 | Extract amount from PDF, save to `user_config` |
| 3 | Generate signed Bank Confirmation |
| 4 | Generate Conversion Order |
| 5 | Generate Salary Invoice (regenerate for current month) |
| 6 | Send three documents to Telegram |
| 7 | Reply to the bank's email in the same thread with all three attachments |

The reply is sent via `send_bank_email_reply`:
- recipient — `bank_email.sender`
- thread — `bank_email.thread_id` (reply appears in the same thread in the bank's Gmail)
- subject — `Re: {original subject}`
- attachments — invoice, bank confirmation, conversion order

`fetch_bank_email_workflow` returns `(Path, BankEmail) | None`.  
In the Telegram handler (`document_handlers.py`), `BankEmail` is not used — no reply is sent there.

---

### `daily_monitoring_summary`

Daily digest from production data.

```
GitHub Actions (cron: 05:00 UTC)
      │  SSH
      ▼
     VPS: docker compose exec finpipe-bot
               │
               ▼
    src/workflows/monitoring/daily_report
               │  reads app_events from last 24h
               ▼
      Telegram monitoring chat
```

**GitHub Actions secrets:**

| Secret | Purpose |
|---|---|
| `VPS_HOST` | VPS address |
| `VPS_USER` | SSH user |
| `VPS_PORT` | SSH port |
| `VPS_SSH_KEY` | Private key |

> ⚠️ Cron runs in UTC. `05:00 UTC` = `07:00` Belgrade time (DST not accounted for).

---

### `check_bank_email`

Monitors incoming bank payment notifications. Runs on cron on days 2–6 of each month.

| Step | Action |
|---|---|
| 1 | Check that today is between the 2nd and 6th |
| 2 | Iterate over all `AllowedUser` records |
| 3 | For each: search for a new bank email via `find_bank_email(telegram_id)` |
| 4 | If found and not yet notified — send a Telegram message to that user |
| 5 | Save marker `notify:{telegram_id}:{message_id}` in `ProcessedMessage` |

- Does not download attachments or mark the email as processed
- Safe to run multiple times — no duplicate notifications
- Marker is cleared when the user resets email history
- If a user has no Gmail connected — silently skipped, continues for others

---

### `backup_database`

Backs up production PostgreSQL.

| Step | Action |
|---|---|
| 1 | Read config: `BACKUP_DIR`, `BACKUP_RETENTION_DAYS` |
| 2 | Create `backups` folder if missing |
| 3 | Run `pg_dump` inside the postgres container |
| 4 | Compress with gzip |
| 5 | Verify the archive exists and is not empty |
| 6 | Delete backups older than `BACKUP_RETENTION_DAYS` |
| 7 | Send status to monitoring chat |

**Key env variables:**

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Connection string |
| `BACKUP_DIR` | Backup directory |
| `BACKUP_RETENTION_DAYS` | Retention period |
| `BACKUP_POSTGRES_SERVICE` | Postgres service name in compose |
| `MONITORING_CHAT_ID` | Where to send status |

---

## Tasks

Tasks are low-level operations used inside workflows and for debugging.

| Task | Purpose |
|---|---|
| `generate_invoice` | Generate Salary Invoice (PDF + DOCX, history recorded) |
| `generate_conversion_order` | Generate signed Conversion Order |
| `generate_bank_confirmation` | Generate signed Bank Confirmation |
| `fetch_bank_email` | Find bank email and download attachments |
| `clear_processed_history` | Reset processed email history |
