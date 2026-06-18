# 🚀 Finpipe

Finpipe — сервис для автоматизации Salary Invoice, Bank Confirmation, Conversion Order и Gmail-сценариев через Telegram.

Вырос из набора локальных скриптов в единый сервис с PostgreSQL-хранилищем, Telegram-ботом и Gmail-интеграцией.

---

## ✨ Возможности

### 📄 Документы

| Документ | Описание |
|---|---|
| Salary Invoice | Генерация счёта на оплату с подстановкой профиля |
| Bank Confirmation | Подтверждение для банка с подписью |
| Conversion Order | Поручение на конвертацию с подписью |

### 📧 Gmail

- Подключение Gmail-аккаунта через OAuth
- Поиск входящих банковских писем (текущий месяц)
- Скачивание PDF-вложений
- Отправка ответных писем через Gmail API

### 🤖 Telegram

- Управление профилем работодателя и реквизитами
- Загрузка и хранение электронной подписи
- Генерация документов прямо из чата
- Подключение и диагностика Gmail
- Статус системы и аудит

---

## 🗄️ База данных

Finpipe использует PostgreSQL.

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/finpipe
```

---

## 🐳 Docker

| Режим | Команда |
|---|---|
| Локально (с проброшенными портами) | `docker compose -f docker-compose.yml -f docker-compose.local.yml up -d` |
| Прод | `docker compose up -d` |

Доступные порты при локальном запуске:

| Сервис | Порт |
|---|---|
| PostgreSQL | `localhost:5433` |
| Web (FastAPI) | `localhost:8000` |

---

## ⚡ Quick Start

```bash
# 1. Установить зависимости
poetry install

# 2. Подготовить .env
cp .env.dist .env

# 3. Применить миграции и создать owner
./scripts/setup_database.sh

# 4. Запустить Telegram-бота
poetry run python src/integrations/telegram/bot.py

# 5. (Опционально) FastAPI для Gmail OAuth
poetry run uvicorn src.interfaces.web.app:app --host 0.0.0.0 --port 8000
```

---

## 📚 Документация

| Раздел | Файл |
|---|---|
| Разработка и отладка | [docs/development.md](docs/development.md) |
| Gmail OAuth | [docs/oauth.md](docs/oauth.md) |
| Хранение данных | [docs/storage.md](docs/storage.md) |
| Мониторинг | [docs/monitoring.md](docs/monitoring.md) |
| Telegram UI | [src/integrations/telegram/README.md](src/integrations/telegram/README.md) |
| Storage ORM | [src/storage/README.md](src/storage/README.md) |
| Workflows | [src/workflows/README.md](src/workflows/README.md) |
| Тесты | [tests/README.md](tests/README.md) |
