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

## Local Development via Cloudflare Tunnel

Для локальной разработки:

1. Поднимите FastAPI локально.
2. Поднимите Cloudflare Quick Tunnel на этот локальный порт.
3. Скопируйте публичный HTTPS URL туннеля.
4. Установите:

`GMAIL_OAUTH_CALLBACK_URL=https://<your-public-host>/oauth/gmail/callback`

5. Тот же URL должен быть зарегистрирован в Google OAuth client settings.

Если tunnel URL меняется, обновить нужно только `GMAIL_OAUTH_CALLBACK_URL` и настройку redirect URI в Google Cloud.
