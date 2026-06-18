# 📧 Gmail OAuth

## 🔄 Сценарий подключения

```
Telegram                     Bot                        Google OAuth
─────────                   ─────                       ────────────
[📧 Gmail → 🔗 Подключить]
                     ──► GmailHandlers.gmail_connect()
                     ──► GmailOAuth.build_authorization_url()
                     ──► OAuthSession сохраняется в БД
                     ◄── inline-кнопка с Google URL
[нажимает 🔗 Подключить Gmail]
                                            ──► Google OAuth consent screen
                                            ◄── redirect → /oauth/gmail/callback
                     GmailOAuthCallbackService.handle_callback()
                     ──► валидация state из OAuthSession
                     ──► code → refresh_token (token exchange)
                     ──► GmailAccount обновляется в БД
                     ──► OAuthSession помечается использованной
                     ──► AuditLog: gmail_oauth_callback SUCCESS
[📊 Статус → ✅ Gmail подключён]
```

---

## 🌐 Callback endpoint

| Параметр | Значение |
|---|---|
| Method | `GET` |
| Path | `/oauth/gmail/callback` |
| Query params | `code`, `state`, `error` |

Route не содержит бизнес-логики — только принимает параметры, делегирует `GmailOAuthCallbackService` и возвращает HTML-ответ.

| Результат | Ответ браузеру |
|---|---|
| ✅ Успех | `Gmail successfully connected. You may close this browser window.` |
| ❌ Ошибка | `Gmail connection failed. <причина>` (HTTP 400) |

Все исходы (успех и ошибка) записываются в `AuditLog` с командой `gmail_oauth_callback`.

---

## ⚙️ Конфигурация

### Callback URL

| Переменная | Назначение |
|---|---|
| `GMAIL_OAUTH_CALLBACK_URL` | Единственный источник callback URL — используется при формировании authorization URL и при token exchange |
| `GMAIL_OAUTH_CALLBACK_ENABLED` | `true` чтобы включить обработку callback |

> ⚠️ Обновление `.env` не обновляет Google Cloud Console. При смене callback URL нужно добавить новый URI в `Authorized redirect URIs` у OAuth Web client.

### OAuth client credentials

Берутся в порядке приоритета:

| Источник | Условие |
|---|---|
| `GMAIL_CLIENT_ID` + `GMAIL_CLIENT_SECRET` | если оба заданы в env |
| `GMAIL_CREDENTIALS_PATH` | fallback — файл `credentials.json` |

### Gmail scopes

```
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.send
```

---

## 🗄️ Хранение токенов

| Таблица | Что хранится |
|---|---|
| `oauth_session` | временная OAuth-сессия (state, expires_at, статус) |
| `gmail_account` | refresh token (зашифрован), gmail_email, last_error |

Refresh token шифруется через `TokenCipher` перед сохранением.

При каждом вызове `get_gmail_service()`:
- токен обновляется через `credentials.refresh(Request())`
- при `RefreshError` — ошибка пишется в `gmail_account.gmail_last_error`, возвращается `None`
- при успехе — `gmail_last_error` очищается

---

## 🛠️ Локальная разработка

Для отладки OAuth через Cloudflare Quick Tunnel:

**1.** Поднять FastAPI локально (обычно `http://127.0.0.1:8000`)

**2.** Запустить туннель:

```bash
./scripts/start_oauth_tunnel.sh
# или с другим портом:
PORT=8080 ./scripts/start_oauth_tunnel.sh
```

Скрипт автоматически:
- запускает `cloudflared tunnel --url http://127.0.0.1:8000`
- формирует `https://<tunnel-host>/oauth/gmail/callback`
- записывает `GMAIL_OAUTH_CALLBACK_URL` в `.env`

**3.** Скопировать напечатанный `OAuth Redirect URI` → добавить в Google Cloud Console → `Authorized redirect URIs`

**4.** Убедиться что в `.env`:
```
GMAIL_OAUTH_CALLBACK_ENABLED=true
GMAIL_OAUTH_CALLBACK_URL=https://<tunnel-host>/oauth/gmail/callback
```

**5.** Telegram → `📧 Gmail` → `🔗 Подключить` → `🔗 Подключить Gmail`

> ⚠️ Quick Tunnel URL меняется при каждом перезапуске скрипта — нужно обновить redirect URI в Google Cloud Console.

---

## 🔍 Диагностика

| Симптом | Что проверить |
|---|---|
| `📊 Статус` показывает `unknown` вместо email | `gmail_account.gmail_email` не заполнен — переподключить |
| `📊 Статус` показывает ошибку | `gmail_account.gmail_last_error` — токен отозван, нужно переподключить |
| Callback недоступен | `GMAIL_OAUTH_CALLBACK_ENABLED=true` в `.env` |
| Ошибка `redirect_uri_mismatch` | callback URL в `.env` не совпадает с Google Cloud Console |
| `AuditLog` показывает FAILED для `gmail_oauth_callback` | ошибка token exchange — проверить логи сервера |
