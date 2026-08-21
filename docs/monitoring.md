# Monitoring

Finpipe records application events in PostgreSQL and sends selected critical events to `MONITORING_CHAT_ID` (or to `BOT_OWNER_TELEGRAM_ID` when no monitoring chat is configured).

The daily summary reports event counts, recent errors, database availability, disk usage, and TLS certificate status when a public domain is configured. Database backup failures are sent immediately to the monitoring chat.

Monitoring services are defined in `infra/monitoring.compose.yml`; the bot itself runs from `docker-compose.yml`.
