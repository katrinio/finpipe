# 🛠️ Development

Локальная разработка, запуск и отладка Finpipe.

---

## 📦 Prerequisites

| Инструмент | Назначение |
|---|---|
| Python 3.14 | Основной язык |
| Poetry | Управление зависимостями |
| PostgreSQL | База данных |
| cloudflared | Gmail OAuth через локальный туннель |

```bash
poetry install
cp .env.dist .env
```

Обязательные переменные в `.env`:

| Переменная | Назначение |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен бота |
| `BOT_OWNER_TELEGRAM_ID` | Telegram ID владельца |
| `SIGNATURE_ENCRYPTION_KEY` | Ключ шифрования подписей |
| `GMAIL_CREDENTIALS_PATH` | Путь к `credentials.json` (или `GMAIL_CLIENT_ID` + `GMAIL_CLIENT_SECRET`) |
| `DATABASE_URL` | Строка подключения к PostgreSQL |

---

## 🚀 Первый запуск

```bash
./scripts/setup_database.sh
```

Скрипт применяет Alembic-миграции и создаёт primary owner. Безопасен для повторного запуска.

---

## 🗄️ Alembic

| Действие | Команда |
|---|---|
| Создать миграцию | `poetry run alembic revision --autogenerate -m "description"` |
| Применить миграции | `poetry run alembic upgrade head` |
| Откатить последнюю | `poetry run alembic downgrade -1` |
| Текущая ревизия | `poetry run alembic current` |
| Актуальные heads | `poetry run alembic heads` |
| История миграций | `poetry run alembic history` |
| Пометить без выполнения | `poetry run alembic stamp head` |

На практике чаще всего нужны только `revision --autogenerate` и `upgrade head`.

---

## 🤖 Telegram Bot

```bash
poetry run python src/integrations/telegram/bot.py
```

Бот читает `DATABASE_URL` и остальные настройки из `.env`.

---

## 🌐 FastAPI

Нужен для обработки Gmail OAuth callback.

```bash
poetry run uvicorn src.interfaces.web.app:app --host 0.0.0.0 --port 8000
```

Проверка:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## 🏗️ Локальная инфраструктура

Для полного локального стенда нужны три процесса:

```
Google OAuth ──► Cloudflare Tunnel ──► FastAPI
                                           ▲
                                    Telegram Bot
```

| Процесс | Команда |
|---|---|
| FastAPI | `poetry run uvicorn src.interfaces.web.app:app --host 0.0.0.0 --port 8000` |
| Telegram Bot | `poetry run python src/integrations/telegram/bot.py` |
| Cloudflare Tunnel | `./scripts/start_oauth_tunnel.sh` |

---

## 📧 Gmail OAuth (локально)

```bash
./scripts/start_oauth_tunnel.sh
# или с другим портом:
PORT=8080 ./scripts/start_oauth_tunnel.sh
```

Скрипт автоматически:
- запускает Cloudflare Quick Tunnel
- формирует `https://<tunnel-host>/oauth/gmail/callback`
- записывает `GMAIL_OAUTH_CALLBACK_URL` в `.env`

Затем:

1. Скопировать `OAuth Redirect URI` из вывода скрипта
2. Добавить в Google Cloud Console → `Authorized redirect URIs`
3. В `.env` установить `GMAIL_OAUTH_CALLBACK_ENABLED=true`
4. Telegram → `📧 Gmail` → `🔗 Подключить`

> ⚠️ Quick Tunnel URL меняется при каждом перезапуске — нужно обновлять Redirect URI в Google Cloud Console.

Подробности: [docs/oauth.md](oauth.md)

---

## 🧪 Тесты

| Команда | Что запускает |
|---|---|
| `poetry run pytest -q` | Все тесты |
| `poetry run pytest tests/unit` | Только unit |
| `poetry run pytest tests/integration` | Только integration |
| `poetry run mypy src` | Типизация |
| `poetry run ruff check .` | Линтер |

---

## 🔍 Отладка

**Health check:**

```bash
curl http://localhost:8000/health
```

**Последние OAuth-сессии:**

```sql
SELECT id, state, telegram_id, status, expires_at, used_at
FROM oauth_sessions
ORDER BY id DESC
LIMIT 5;
```

**Последние Gmail-подключения:**

```sql
SELECT id, owner_telegram_id,
       gmail_refresh_token IS NOT NULL AS has_token,
       gmail_connected_at, gmail_last_error
FROM gmail_account
ORDER BY id DESC
LIMIT 5;
```

---

## 🚨 Troubleshooting

| Симптом | Решение |
|---|---|
| `Cloudflare Error 1033` | Tunnel не достучался до FastAPI — проверить `curl http://localhost:8000/health` |
| `redirect_uri_mismatch` | Обновить Redirect URI в Google Cloud Console под текущий tunnel URL |
| `OAuth callback returns 400` | Убедиться что flow запущен через `Connect Gmail`, не через прямой переход |
| `callback flow is disabled` | В `.env`: `GMAIL_OAUTH_CALLBACK_ENABLED=true` и `GMAIL_OAUTH_CALLBACK_URL=https://...` |
