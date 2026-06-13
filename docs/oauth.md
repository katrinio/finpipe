# Gmail OAuth

## Flow

Рабочий сценарий подключения Gmail выглядит так:

1. Пользователь в Telegram нажимает `📧 Gmail` -> `🔗 Подключить`.
2. `GmailHandlers.gmail_connect()` вызывает существующий `GmailOAuth.build_authorization_url(...)`.
3. OAuth state сохраняется в `OAuthSession`.
4. Google перенаправляет браузер на `GET /oauth/gmail/callback`.
5. FastAPI route передаёт обработку в `GmailOAuthCallbackService`.
6. Сервис валидирует `state`, обменивает `code` на токены, сохраняет refresh token и обновляет `GmailAccount`.
7. `OAuthSession` помечается использованной.
8. Статус Gmail в Telegram становится `Connected`.

## Callback Endpoint

FastAPI endpoint:

`GET /oauth/gmail/callback`

Параметры:

- `code`
- `state`
- `error`

Route не содержит бизнес-логики. Он только:

- принимает query params;
- вызывает `GmailOAuthCallbackService`;
- возвращает пользователю понятный текстовый ответ.

Успех:

`Gmail successfully connected.`

`You may close this browser window.`

Ошибка:

`Gmail connection failed.`

с краткой причиной.

## Configuration

Единственный источник callback URL:

`GMAIL_OAUTH_CALLBACK_URL`

Эта переменная используется:

- при формировании Google OAuth authorization URL;
- при обработке callback и token exchange.

Не нужно хардкодить Cloudflare Tunnel URL в коде.

## Local Development

Для локальной отладки Gmail OAuth через Cloudflare Quick Tunnel:

1. Поднимите FastAPI локально, обычно на `http://127.0.0.1:8000`.
2. Запустите bootstrap-скрипт:

```bash
./scripts/start_oauth_tunnel.sh
```

3. Скрипт:
   - запускает `cloudflared tunnel --url http://127.0.0.1:8000`;
   - извлекает публичный `trycloudflare.com` URL;
   - формирует callback:
     `https://<tunnel-host>/oauth/gmail/callback`
   - записывает его в корневой `.env` как `GMAIL_OAUTH_CALLBACK_URL=...`
   - печатает `Tunnel URL` и `OAuth Redirect URI`.

4. Возьмите напечатанный `OAuth Redirect URI` и добавьте его в Google OAuth client settings.
5. Убедитесь, что `GMAIL_OAUTH_CALLBACK_ENABLED=true`.
6. После этого можно запускать сценарий:
   - Telegram -> `📧 Gmail` -> `🔗 Подключить`
   - Google OAuth
   - callback в локальный FastAPI через tunnel

Если FastAPI слушает другой порт, перед запуском скрипта задайте:

```bash
PORT=8080 ./scripts/start_oauth_tunnel.sh
```

Если tunnel URL меняется, достаточно снова запустить скрипт и обновить redirect URI в Google Cloud.
