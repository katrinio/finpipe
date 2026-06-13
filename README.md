# FINPIPE

Finpipe — сервис для автоматизации Salary Invoice, Bank Confirmation, Conversion Order и Gmail-сценариев через Telegram.

Проект вырос из набора локальных скриптов в единый сервис с:

- Telegram-ботом
- SQLite-хранилищем
- пользовательскими профилями
- Gmail-интеграцией
- историей генерации документов

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

- Development: [docs/development.md](/Users/katrin/PycharmProjects/finpipe/docs/development.md)
- Gmail OAuth: [docs/oauth.md](/Users/katrin/PycharmProjects/finpipe/docs/oauth.md)
- Storage: [docs/storage.md](/Users/katrin/PycharmProjects/finpipe/docs/storage.md)
- Telegram UI: [src/integrations/telegram/README.md](/Users/katrin/PycharmProjects/finpipe/src/integrations/telegram/README.md)

