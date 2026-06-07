# Storage

`src/storage/storage.sqlite3` хранит локальное состояние проекта.

## ORM structure

По аналогии с `permafor` ORM вынесен в отдельный пакет `src/storage/orm/`:

- `base.py` - общий `DeclarativeBase`
- `history_record.py` - сущность истории инвойсов
- `processed_message.py` - сущность обработанных писем
- `__init__.py` - re-export ORM-сущностей

## Схема

- `invoice_history`
  - `invoice_number TEXT PRIMARY KEY`
  - `created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `processed_messages`
  - `message_id TEXT PRIMARY KEY`
  - `created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`

## ORM entities

- `HistoryRecord` -> `invoice_history`
- `ProcessedMessage` -> `processed_messages`

Сейчас связей между сущностями нет. Новые сущности вроде `Invoice`, `BankRequest`, `EmailHistory` и `AuditLog`
можно добавлять как отдельные ORM-модули внутри `src/storage/orm/` и отдельные explicit repositories.

## Поток инициализации

1. Composition root вызывает `build_storage_dependencies()`.
2. `Database` создаёт engine и `sessionmaker`.
3. `Database.initialize_schema()` создаёт ORM-таблицы через `BaseStorage.metadata.create_all(...)`.
4. Workflow получает готовые repository-абстракции и работает только через них.

## Session lifecycle

Каждый repository-метод открывает короткоживущую `Session`, выполняет одну операцию и закрывает её.
Commit/rollback управляется явно внутри infrastructure-слоя. В приложении и workflow `Session` не видна.

## TODO

При появлении нескольких версий схемы заменить `create_all` на Alembic migration chain.
