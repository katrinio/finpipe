# Storage

`src/storage/storage.sqlite3` хранит локальное состояние проекта.

##  Structure
```
storage/
├── database.py
├── dependencies.py
├── orm/
├── repositories/
└── storage.sqlite3
```
# Storage

src/storage/storage.sqlite3 хранит локальное состояние проекта.

## Structure

text storage/ ├── database.py ├── dependencies.py ├── orm/ ├── repositories/ └── storage.sqlite3

### database.py

Создаёт SQLAlchemy engine, sessionmaker и инициализирует схему БД.

### dependencies.py

Composition root для storage-слоя. Создаёт и возвращает готовые repository-зависимости.

### orm/

SQLAlchemy ORM-модели.

- base.py — общий DeclarativeBase
- history_record.py — история сгенерированных инвойсов
- processed_message.py — обработанные письма банка
- telegram_update.py — обработанные Telegram updates
- user_config.py — пользовательские настройки

Каждая ORM-модель располагается в отдельном файле.

### repositories/

Репозитории для доступа к данным.

Репозитории скрывают SQLAlchemy от application-слоя и предоставляют высокоуровневые операции для workflow.

## Database schema

### invoice_history

| Column | Type |
|----------|----------|
| invoice_number | TEXT PRIMARY KEY |
| created_at | DATETIME NOT NULL |

### processed_messages

| Column | Type |
|----------|----------|
| message_id | TEXT PRIMARY KEY |
| created_at | DATETIME NOT NULL |

### telegram_updates

| Column | Type |
|----------|----------|
| update_id | INTEGER PRIMARY KEY |
| created_at | DATETIME NOT NULL |

## Initialization flow

1. Workflow вызывает build_storage_dependencies().
2. Создаётся Database.
3. Инициализируется SQLAlchemy engine.
4. ORM-схема создаётся через Base.metadata.create_all(...).
5. Workflow получает готовые repository-объекты.

## Session lifecycle

Каждая repository-операция открывает собственную короткоживущую Session.

Repository отвечает за:

- создание Session;
- commit;
- rollback;
- закрытие Session.

Workflow и сервисы не работают напрямую с SQLAlchemy Session.

## Future improvements

- Alembic migrations
- User configuration storage
- Audit log
- Bank request history
- Email history
