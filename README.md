# Finpipe

Персональный сервис для автоматизации документооборота ИП: генерация Salary Invoice, Bank Confirmation, Conversion Order, интеграция с Gmail и Telegram-бот для управления всем из чата.

---

## Возможности

### Документы

| Документ | Описание |
|---|---|
| Salary Invoice | Счёт на оплату с подстановкой профиля и подписи |
| Bank Confirmation | Подтверждение для банка с электронной подписью |
| Conversion Order | Поручение на конвертацию с подписью |

### Банковский день

Один сценарий закрывает весь цикл банковского платежа:
1. Поиск письма банка в Gmail
2. Извлечение суммы из PDF
3. Генерация Bank Confirmation, Conversion Order и Salary Invoice
4. Отправка документов в Telegram
5. Ответ банку с документами в копии

### Gmail

- OAuth-авторизация
- Поиск входящих банковских писем
- Отправка ответов с вложениями через Gmail API

### Telegram

- Управление профилем работодателя и банковскими реквизитами
- Загрузка и хранение электронной подписи (зашифрована)
- Генерация документов из чата
- Мониторинговый чат с диагностическими командами

---

## Стек

- Python 3.14, Poetry
- PostgreSQL + SQLAlchemy + Alembic
- Telegram Bot API (polling)
- Gmail API (OAuth 2.0)
- Docker Compose

---

## Быстрый старт

```bash
poetry install
cp .env.dist .env
# заполнить .env
./scripts/setup_database.sh
poetry run python src/integrations/telegram/bot.py
```

Для Gmail OAuth (локально):

```bash
./scripts/start_local_oauth_stack.sh
```

---

## Docker

```bash
# Прод
docker compose up -d

# Локально (с проброшенными портами)
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

---

## Документация

| Раздел | Файл |
|---|---|
| Разработка и отладка | [docs/development.md](docs/development.md) |
| Gmail OAuth | [docs/oauth.md](docs/oauth.md) |
| Хранение данных | [docs/storage.md](docs/storage.md) |
| Мониторинг | [docs/monitoring.md](docs/monitoring.md) |
