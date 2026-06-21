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
| `EMAIL_DRY_RUN` | `true` — письма не отправляются (для разработки и CI) |
| `EMAIL_DRY_RUN_RECIPIENT` | Email для тестовой отправки (когда `EMAIL_DRY_RUN=false`) |

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

---

## 🎛️ Telegram UI

Бот использует **reply keyboard** для навигации.

### Структура меню

```
/start → Главное меню
├── 📄 Документы
│   ├── 🧾 Инвойс
│   │   ├── 💰 Указать сумму
│   │   ├── 💶 Текущая сумма
│   │   └── 📄 Создать инвойс → [📤 Отправить компании | ✖️ Не отправлять]
│   └── 🏦 Банковский день → инфо-экран [▶️ Запустить | 🏠 Домой]
│       └── ▶️ Запустить → workflow → [📤 Ответить банку | ✖️ Не отправлять]
├── 📧 Интеграции → Gmail-меню напрямую
│   ├── 🔗 Подключить / ❌ Отключить
│   ├── 📊 Статус
│   ├── 🏠 Домой
│   └── 🗑 Сбросить историю → подтверждение [🗑 Да, сбросить | ✖️ Не отправлять]
├── 👤 Мой профиль
│   ├── 👁 Посмотреть профиль / 👤 Кто я
│   ├── 📥 Скачать шаблон / 📤 Обновить профиль
│   ├── ✍️ Загрузить подпись / 🗑 Удалить подпись
│   └── 🏠 Домой
└── 📖 Справка
    ├── ❓ Как начать / ✅ Готовность
    └── 🏠 Домой
```

### Принцип разделения кнопок

- **Reply keyboard** — навигация между разделами
- **One-time reply keyboard** — выбор внутри одного действия (отправить/пропустить)

### Общие константы кнопок

`NavigationButtons.HOME` — кнопка возврата в главное меню (используется во всех подменю).
`NavigationButtons.SKIP` — кнопка `✖️ Не отправлять` (используется в промптах инвойса и банковского дня).

### Иконки статусов

| Иконка | Смысл | Где используется |
|---|---|---|
| ✅ | Набор проверок пройден — всё готово | Итог операции (`MsgIcon.success`) |
| ✔️ | Отдельный пункт чеклиста ок | Пункты в списке готовности (`MsgIcon.status`) |
| ❌ | Итог операции — провал | Итог операции (`MsgIcon.error`) |
| ❗ | Отдельный пункт чеклиста не ок | Пункты в списке готовности (`MsgIcon.status`) |
| ➖ | Частично заполнено | Поля профиля (частичное заполнение) |

Правило: `✅`/`❌` — для итога действия или набора. `✔️`/`❗` — для отдельного пункта внутри списка.

### Банковский день

Нажатие «🏦 Банковский день» открывает инфо-экран со статусом готовности:
- ✔️/❗ Профиль (компания + реквизиты)
- ✔️/❗ Подпись
- ✔️/❗ Gmail

После нажатия «▶️ Запустить» workflow генерирует три документа и отправляет их в чат. Ответ на письмо банка отправляется всем получателям оригинала (To + CC).

Если пользователь нажимает `✖️ Не отправлять` — оба ключа в `ProcessedMessage` снимаются, письмо можно обработать снова, мониторинг уведомит повторно.

### Синхронизация ProcessedMessage

Таблица `processed_messages` используется двумя системами с разными ключами:

| Ключ | Кто пишет | Смысл |
|---|---|---|
| `{message_id}` | `fetch_bank_email_workflow` | письмо скачано и обработано банковским днём |
| `notify:{telegram_id}:{message_id}` | `check_bank_email` (cron) | пользователь уже получил уведомление |

Когда банковский день обрабатывает письмо — ставятся оба ключа (мониторинг не уведомит повторно). Когда пользователь пропускает ответ — снимаются оба ключа (письмо можно обработать снова, мониторинг уведомит при следующем запуске крона).
