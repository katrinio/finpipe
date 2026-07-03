# 📡 Monitoring

Finpipe использует два уровня мониторинга: **Grafana** для метрик и аптайма, **Telegram-чат** для критических бизнес-алертов.

---

## 🎯 Разделение ответственности

| Grafana | Telegram monitoring chat |
|---|---|
| Аптайм и доступность сервера | Бэкап не создался |
| CPU, память, диск | Инвойс не отправился |
| Общие метрики приложения | Ошибка обработки письма банка |
| Дашборды и графики | Ошибка подключения Gmail |

Telegram-чат — **alert-only**: получает только те события, которые требуют немедленного внимания и не покрыты Grafana.

---

## ⚙️ Как это работает

```
Системное событие
       │
       ▼
  EventLogger ──► app_events (PostgreSQL) ──► Grafana
       │
       └── критические события ──► Telegram monitoring chat
```

Таблица `app_events` — единый журнал всех событий. Grafana читает его напрямую. Telegram получает только allowlist критических типов.

---

## 🔴 Алерты в Telegram

В чат попадают только события из allowlist:

| Событие | Когда |
|---|---|
| `backup_failed` | Не создался бэкап БД |
| `invoice_send_failed` | Не отправился инвойс компании |
| `bank_email_processing_failed` | Ошибка в сценарии банковского дня |
| `gmail_connect_failed` | Провал OAuth при подключении Gmail |

Все остальные события (генерация документов, настройки, рестарт бота) хранятся только в `app_events` и видны через Grafana.

---

## 📨 Куда отправляются алерты

| Приоритет | Назначение |
|---|---|
| 1 | `MONITORING_CHAT_ID` (если задан) |
| 2 | `BOT_OWNER_TELEGRAM_ID` (fallback) |

---

## 📝 Формат алерта

```
Monitoring event: invoice_send_failed
Severity: error
Details: {"telegram_id": 123, "error": "SMTP timeout"}
```

---

## 🛠️ Команды мониторингового чата

Чат работает в режиме alert-only. Единственная команда:

| Команда | Описание |
|---|---|
| `/chatid` | ID текущего чата (для первичной настройки `MONITORING_CHAT_ID`) |

Текст и неизвестные команды игнорируются.

---

## 🔒 Изоляция

| Правило | Описание |
|---|---|
| Входящие из monitoring chat не попадают в user router | Нет конфликтов с пользовательскими командами |
| Пользовательские состояния не обрабатываются | Не портит Telegram workflow |
| Обычный текст и неизвестные команды игнорируются | Чат можно использовать для обсуждения |

Grafana читает PostgreSQL Finpipe через общую Docker network `finpipe-shared`. База при этом не публикуется наружу.

---

## 🏗️ Архитектура

| Компонент | Назначение |
|---|---|
| `EventLogger` | Регистрация событий, запись в `app_events` |
| `app_events` | Таблица-журнал всех событий (источник для Grafana) |
| `notifications.py` — `_CHAT_EVENTS` | Allowlist событий для Telegram |
| `register_monitoring_notifications()` | Подписка на EventLogger при старте бота |

---

## 🔑 Проверка Gmail-токенов

Gmail OAuth токены периодически истекают. Cron-задача проверяет их для всех подключённых пользователей и пишет напрямую в чат пользователя — не в мониторинговый.

```
VPS cron (ежедневно, 09:00)
       │
       ▼
src/workflows/monitoring/check_gmail_tokens.py
       │
       ├── токен OK → ничего
       └── RefreshError → сообщение в личный чат пользователя:
           "⚠️ Gmail отключился — переподключите в разделе «Gmail»"
```

Добавить в crontab на VPS:

```bash
0 9 * * * cd ~/projects/finpipe && docker compose exec -T finpipe-bot python -m src.workflows.monitoring.check_gmail_tokens >> ~/logs/gmail-check.log 2>&1
```

---

## 📊 Ежедневная сводка

Отдельно от live-алертов работает ежедневный отчёт.

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
         app_events (prod PostgreSQL, последние 24ч)
                  │
                  ▼
         Telegram monitoring chat
```

**Расписание:** `05:00 UTC` (07:00 по Белграду, без учёта DST).

> ⚠️ При смене DST cron-расписание нужно пересматривать вручную.
