Development

Локальная разработка, запуск и отладка Finpipe.

⸻

📦 Prerequisites

Нужно установить:

* Python 3.14
* Poetry
* SQLite
* cloudflared (для локальной Gmail OAuth разработки)

Подготовка окружения:

poetry install
cp .env.dist .env

Заполнить .env:

* TELEGRAM_BOT_TOKEN
* owner/admin настройки
* SIGNATURE_ENCRYPTION_KEY
* GMAIL_CREDENTIALS_PATH

⸻

🚀 Первый запуск

Создать или обновить структуру БД:

./scripts/setup_database.sh

Скрипт:

* применяет Alembic миграции;
* создаёт primary owner пользователя;
* безопасен для повторного запуска.

⸻

🗄️ Alembic

Создать новую миграцию:

poetry run alembic revision --autogenerate -m "description"

Применить миграции:

poetry run alembic upgrade head

Откатить последнюю миграцию:

poetry run alembic downgrade -1

Посмотреть текущее состояние:

poetry run alembic current
poetry run alembic heads
poetry run alembic history

⸻

🤖 Run Telegram Bot

poetry run python src/integrations/telegram/bot.py

Бот использует:

data/finpipe.db

и настройки из .env.

⸻

🌐 Run FastAPI

Нужен для Gmail OAuth callback.

poetry run uvicorn src.interfaces.web.app:app --host 0.0.0.0 --port 8000

⸻

❤️ Health Check

Проверка, что web-слой поднялся:

curl http://localhost:8000/health

Ожидаемый ответ:

{"status":"ok"}

⸻

🏗️ Локальная инфраструктура

Обычно достаточно трёх процессов:

1. FastAPI
2. Telegram Bot
3. Cloudflare Tunnel

FastAPI ← Cloudflare Tunnel ← Google OAuth
     ↑
 Telegram Bot

TODO(vps): заменить Cloudflare Tunnel постоянным доменом после переезда на VPS.

⸻

📧 Gmail OAuth Development

Локальный flow:

1. Поднять FastAPI
2. Запустить tunnel
3. Получить публичный URL
4. Обновить Redirect URI в Google Cloud
5. Нажать Integrations → Gmail → Connect Gmail
6. Пройти Google Consent Screen
7. Дождаться callback

Подробности:

docs/oauth.md

⸻

🔗 start_oauth_tunnel.sh

Для локальной OAuth-разработки:

./scripts/start_oauth_tunnel.sh

Скрипт:

* запускает Cloudflare Quick Tunnel;
* получает публичный URL;
* формирует OAuth callback URL;
* обновляет локальную конфигурацию;
* печатает готовый Redirect URI.

Пример:

Tunnel URL:
https://example.trycloudflare.com
OAuth Redirect URI:
https://example.trycloudflare.com/oauth/gmail/callback

Другой порт:

PORT=8080 ./scripts/start_oauth_tunnel.sh

После каждого нового tunnel URL необходимо обновить:

Google Cloud Console
→ APIs & Services
→ Credentials
→ OAuth Web Client
→ Authorized Redirect URIs

⸻

🔍 Debugging

Health:

curl http://localhost:8000/health

Последние OAuth sessions:

sqlite3 data/finpipe.db \
"SELECT id,state,telegram_id,status,expires_at,used_at
FROM oauth_sessions
ORDER BY id DESC
LIMIT 5;"

Последние Gmail подключения:

sqlite3 data/finpipe.db \
"SELECT id,
        owner_telegram_id,
        gmail_refresh_token IS NOT NULL,
        gmail_connected_at,
        gmail_last_error
FROM gmail_account
ORDER BY id DESC
LIMIT 5;"

⸻

🧪 Testing

Все тесты:

poetry run pytest -q

Типизация:

poetry run mypy src

Линтер:

poetry run ruff check .

⸻

🚨 Troubleshooting

Cloudflare Error 1033

Tunnel не может достучаться до FastAPI.

Проверить:

curl http://localhost:8000/health

⸻

redirect_uri_mismatch

Google OAuth Redirect URI не совпадает с текущим tunnel URL.

Решение:

1. Перезапустить tunnel
2. Скопировать новый Redirect URI
3. Обновить его в Google Cloud Console

⸻

OAuth callback returns 400

Проверить:

* flow запущен через Connect Gmail;
* callback не открыт повторно;
* в oauth_sessions появилась новая запись.

⸻

Gmail connect requested while callback flow is disabled

В .env должно быть:

GMAIL_OAUTH_CALLBACK_ENABLED=true
GMAIL_OAUTH_CALLBACK_URL=https://...