# FINPIPE

Finpipe — сервис для автоматизации Salary Invoice, Bank Confirmation, Conversion Order и Gmail-сценариев через Telegram.

Проект вырос из набора локальных скриптов в единый сервис с:

- Telegram-ботом
- PostgreSQL-хранилищем
- пользовательскими профилями
- Gmail-интеграцией
- историей генерации документов

## Database

Finpipe uses PostgreSQL.

Example:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/finpipe
```

## Main Features

### Documents

- Salary Invoice
- Bank Confirmation
- Conversion Order
- автоматическая подстановка пользовательских данных
- вставка электронной подписи

### Gmail

- подключение Gmail-аккаунта
- поиск банковских писем
- скачивание PDF-вложений
- отправка писем через Gmail API

### Telegram

Через Telegram доступны:

- профиль пользователя
- подпись
- генерация документов
- Gmail integration
- статус профиля и системы

## Docker

Базовый файл `docker-compose.yml` содержит общую конфигурацию сервисов и используется в проде.
`docker-compose.local.yml` добавляет проброс портов для локальной разработки.

**Локально:**

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

Доступные порты:
- PostgreSQL: `localhost:5433`
- Web (FastAPI): `localhost:8000`

**На сервере (прод):**

```bash
docker compose up -d
```

## Quick Start

1. Установить зависимости:

```bash
poetry install
```

2. Подготовить `.env`

3. Запустить Telegram-бота:

```bash
poetry run python src/integrations/telegram/bot.py
```

4. При необходимости поднять FastAPI для OAuth callback:

```bash
poetry run uvicorn src.interfaces.web.app:app --host 0.0.0.0 --port 8000
```

## Documentation

- Development: [docs/development.md](docs/development.md)
- Gmail OAuth: [docs/oauth.md](docs/oauth.md)
- Storage: [docs/storage.md](docs/storage.md)
- Telegram UI: [src/integrations/telegram/README.md](src/integrations/telegram/README.md)
