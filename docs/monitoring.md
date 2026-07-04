# Monitoring

Finpipe uses two layers of monitoring: **Grafana** for metrics and uptime, **Telegram chat** for critical business alerts.

---

## Responsibilities

| Grafana | Telegram monitoring chat |
|---|---|
| Server uptime and availability | Backup failed |
| CPU, memory, disk | Invoice not sent |
| General app metrics | Bank email processing error |
| Dashboards and graphs | Gmail connection failed |

The Telegram chat is **alert-only** — it receives only events that need immediate attention and aren't covered by Grafana.

---

## How it works

```
System event
      │
      ▼
 EventLogger ──► app_events (PostgreSQL) ──► Grafana
      │
      └── critical events ──► Telegram monitoring chat
```

`app_events` is the single event log. Grafana reads it directly. Telegram receives only the events in the allowlist.

---

## Telegram alerts

Only events from the allowlist reach the chat:

| Event | When |
|---|---|
| `backup_failed` | Database backup failed |
| `invoice_send_failed` | Invoice not sent to company |
| `bank_email_processing_failed` | Error in bank day workflow |
| `gmail_connect_failed` | OAuth failure when connecting Gmail |

All other events (document generation, settings changes, bot restarts) are stored in `app_events` only and visible through Grafana.

---

## Where alerts go

| Priority | Destination |
|---|---|
| 1 | `MONITORING_CHAT_ID` (if set) |
| 2 | `BOT_OWNER_TELEGRAM_ID` (fallback) |

---

## Alert format

```
Monitoring event: invoice_send_failed
Severity: error
Details: {"telegram_id": 123, "error": "SMTP timeout"}
```

---

## Monitoring chat commands

The chat operates in alert-only mode. One command available:

| Command | Description |
|---|---|
| `/chatid` | Returns the current chat ID (for initial `MONITORING_CHAT_ID` setup) |

Other text and unknown commands are ignored.

---

## Isolation

| Rule | Description |
|---|---|
| Monitoring chat input doesn't reach the user router | No conflicts with user commands |
| User states are not processed | Doesn't interfere with Telegram workflows |
| Unknown text and commands are ignored | The chat can be used for discussion |

Grafana reads the Finpipe PostgreSQL database through the shared Docker network `finpipe-shared`. The database is not exposed externally.

---

## Architecture

| Component | Purpose |
|---|---|
| `EventLogger` | Records events, writes to `app_events` |
| `app_events` | Event log table (Grafana data source) |
| `notifications.py` — `_CHAT_EVENTS` | Allowlist of events for Telegram |
| `register_monitoring_notifications()` | Subscribes to EventLogger on bot startup |

### Infrastructure config

Grafana, Prometheus, Loki, and Alloy are defined in `infra/`:

| File | Purpose |
|---|---|
| `infra/monitoring.compose.yml` | Docker Compose for the monitoring stack |
| `infra/prometheus.yml` | Prometheus scrape config |
| `infra/alloy-config.alloy` | Alloy config — Docker log collection → Loki |

Start the monitoring stack:

```bash
docker compose -f infra/monitoring.compose.yml up -d
```

---

## Gmail token check

Gmail OAuth tokens expire periodically. A cron job checks them for all connected users and sends a message directly to each user's own chat — not the monitoring chat.

```
VPS cron (daily, 09:00)
      │
      ▼
src/workflows/monitoring/check_gmail_tokens.py
      │
      ├── token OK → nothing
      └── RefreshError → message to user's chat:
          "⚠️ Gmail disconnected — reconnect in the Gmail section"
```

Add to crontab on VPS:

```bash
0 9 * * * cd ~/projects/finpipe && docker compose exec -T finpipe-bot python -m src.workflows.monitoring.check_gmail_tokens >> ~/logs/gmail-check.log 2>&1
```

---

## Daily report

A separate daily digest runs on a schedule.

```
GitHub Actions (cron, 05:00 UTC)
      │  SSH
      ▼
     VPS: docker compose exec finpipe-bot
               │
               ▼
    src/workflows/monitoring/daily_report
               │
               ▼
      app_events (prod PostgreSQL, last 24h)
               │
               ▼
      Telegram monitoring chat
```

**Schedule:** `05:00 UTC` (07:00 Belgrade time, DST not accounted for).

> ⚠️ When DST changes, update the cron schedule manually.
