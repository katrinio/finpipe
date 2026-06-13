# Development

Этот документ нужен для локальной разработки, запуска и отладки Finpipe.

## Prerequisites

Нужно иметь:

- Python 3.14
- Poetry
- SQLite
- `cloudflared` для локальной OAuth-разработки

Подготовка окружения:

```bash
poetry install
cp .env.dist .env
```

После этого заполните `.env` нужными значениями:

- Telegram bot token
- owner/admin settings
- `SIGNATURE_ENCRYPTION_KEY`
- `GMAIL_CREDENTIALS_PATH`

## Run Telegram Bot

Локальный запуск бота:

```bash
poetry run python src/integrations/telegram/bot.py
```

Бот использует SQLite из `data/finpipe.db` и читает настройки из `.env`.

## Run FastAPI

FastAPI нужен для OAuth callback.

Запуск:

```bash
poetry run uvicorn src.interfaces.web.app:app --host 0.0.0.0 --port 8000
```

## Health Check

Проверка, что web-слой поднят:

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

## Local Infrastructure

Для локальной разработки обычно достаточно трёх процессов:

1. FastAPI
2. Telegram bot
3. Cloudflare Tunnel для Gmail OAuth callback

TODO(vps): после появления VPS описать production-like запуск через постоянный домен вместо Cloudflare Tunnel.

## Testing

Запуск всех тестов:

```bash
poetry run pytest -q
```

Типизация:

```bash
poetry run mypy src
```

Линтер:

```bash
poetry run ruff check .
```

## Gmail OAuth Development

Локальный OAuth flow выглядит так:

1. Поднять FastAPI.
2. Поднять Cloudflare Quick Tunnel.
3. Получить публичный callback URL.
4. Обновить Redirect URI в Google Cloud Console.
5. В Telegram нажать:
   `Integrations` -> `Gmail` -> `Connect Gmail`
6. Пройти Google consent screen.
7. Дождаться callback в локальный FastAPI.

Подробнее про сам OAuth flow: [oauth.md](/Users/katrin/PycharmProjects/finpipe/docs/oauth.md)

### OAuth Callback Endpoint

Используется маршрут:

`GET /oauth/gmail/callback`

Он принимает:

- `code`
- `state`
- `error`

И передаёт обработку в существующий Gmail OAuth callback service.

## start_oauth_tunnel.sh

Для локальной OAuth-разработки используется:

TODO(vps): оставить `start_oauth_tunnel.sh` как dev-only инструмент и убрать его из основного сценария запуска.

```bash
./scripts/start_oauth_tunnel.sh
```

Этот скрипт:

- запускает Cloudflare Quick Tunnel;
- получает публичный URL из `cloudflared`;
- формирует callback URL вида:
  `https://<tunnel-host>/oauth/gmail/callback`
- обновляет локальную конфигурацию через `.env`
- печатает готовый Redirect URI для Google OAuth

Пример результата:

```text
Tunnel URL:
https://example.trycloudflare.com
OAuth Redirect URI:
https://example.trycloudflare.com/oauth/gmail/callback
```

Если FastAPI слушает не `8000`, можно передать порт:

```bash
PORT=8080 ./scripts/start_oauth_tunnel.sh
```

После каждого нового tunnel URL нужно скопировать напечатанный `OAuth Redirect URI` в Google Cloud Console:

`APIs & Services` -> `Credentials` -> OAuth Web client -> `Authorized redirect URIs`

Для Telegram OAuth используются `GMAIL_CLIENT_ID` и `GMAIL_CLIENT_SECRET` из `.env`. Если они не заданы, код использует `GMAIL_CREDENTIALS_PATH` как fallback.

## Debugging

Полезные точки проверки во время разработки:

- health endpoint:
  `curl http://localhost:8000/health`
- OAuth sessions в SQLite:
  `sqlite3 data/finpipe.db`
- логи приложения:
  `logs/app.log`

Для проверки состояния OAuth удобно смотреть:

```bash
sqlite3 data/finpipe.db "SELECT id,state,telegram_id,status,expires_at,used_at FROM oauth_sessions ORDER BY id DESC LIMIT 5;"
```

И Gmail account:

```bash
sqlite3 data/finpipe.db "SELECT id,owner_telegram_id,gmail_refresh_token IS NOT NULL,gmail_connected_at,gmail_last_error FROM gmail_account ORDER BY id DESC LIMIT 5;"
```

## Troubleshooting

### Cloudflare Error 1033

Причина:

Tunnel не может достучаться до локального FastAPI.

Проверка:

```bash
curl http://localhost:8000/health
```

Если health endpoint не отвечает, сначала поднимите FastAPI.

### redirect_uri_mismatch

Причина:

Google OAuth Redirect URI не совпадает с текущим tunnel URL.

Решение:

1. Перезапустить `./scripts/start_oauth_tunnel.sh`
2. Скопировать новый `OAuth Redirect URI`
3. Обновить `Authorized redirect URIs` в Google Cloud Console

Проверка:

- OAuth URL должен содержать тот же `redirect_uri`, что и `GMAIL_OAUTH_CALLBACK_URL`;
- этот URI должен быть добавлен именно в Web OAuth client в Google Cloud Console.

### OAuth callback returns 400

Причина:

Отсутствует `code` или `state`, либо callback открыт повторно с уже использованным state.

Проверить:

- действительно ли flow начался через `Connect Gmail`
- не был ли открыт старый callback URL
- есть ли новая запись в `oauth_sessions`

### Gmail connect requested while callback flow is disabled

Причина:

Не включён OAuth callback flow.

Решение:

Добавить в `.env`:

```dotenv
GMAIL_OAUTH_CALLBACK_ENABLED=true
```

И убедиться, что задан `GMAIL_OAUTH_CALLBACK_URL`.
