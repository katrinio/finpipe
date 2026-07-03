# Finpipe
Если вы ИП и каждый месяц вручную заполняете одни и те же документы для банка — это сделано для вас.

Finpipe — Telegram-бот, который берёт на себя рутину вокруг зарплатного платежа. Пришло письмо от банка — бот найдёт его в Gmail, вытащит сумму, заполнит три документа с подписью и пришлёт вам в чат. Всё это можно запустить с телефона, не открывая ноутбук.

![](docs/header.svg)


---

## Что умеет

### Банковский день

Один сценарий — весь цикл банковского платежа:

1. Находит письмо банка в Gmail
2. Извлекает сумму из PDF
3. Генерирует Bank Confirmation, Conversion Order и Salary Invoice с подписью
4. Отправляет документы в Telegram
5. Предлагает отправить ответ банку с документами в приложении

Запустить можно с телефона — компьютер не нужен.

### Документы

| Документ | Описание |
|---|---|
| Salary Invoice | Счёт на оплату с подстановкой профиля и подписи |
| Bank Confirmation | Подтверждение для банка с электронной подписью |
| Conversion Order | Поручение на конвертацию с подписью |

### Gmail

- OAuth-авторизация
- Поиск входящих писем банка
- Отправка ответов с вложениями через Gmail API
- Уведомление в чат, если токен истёк и нужно переподключиться

### Telegram

- Управление профилем работодателя и банковскими реквизитами
- Загрузка и хранение электронной подписи (зашифрована)
- Генерация документов из чата
- Мониторинговый чат для алертов

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
# Основной стек Finpipe
docker compose up -d

# Локально (с проброшенными портами)
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d

# Стек мониторинга
docker compose -f monitoring.compose.yml up -d
```

---

## Документация

| Раздел | Файл |
|---|---|
| Разработка и отладка | [docs/development.md](docs/development.md) |
| Gmail OAuth | [docs/oauth.md](docs/oauth.md) |
| Хранение данных | [docs/storage.md](docs/storage.md) |
| Мониторинг | [docs/monitoring.md](docs/monitoring.md) |
