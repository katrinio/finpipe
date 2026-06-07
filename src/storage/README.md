# Storage

`src/storage/storage.sqlite3` хранит локальное состояние проекта.

## Схема

- `invoice_history`
  - `invoice_number TEXT PRIMARY KEY`
  - `created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `processed_messages`
  - `message_id TEXT PRIMARY KEY`
  - `created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `applied_migrations`
  - `migration_name TEXT PRIMARY KEY`
  - `applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`

## ORM-модели

- `HistoryRecord` -> `invoice_history`
- `ProcessedMessage` -> `processed_messages`
- `AppliedMigration` -> `applied_migrations`

Сейчас связей между сущностями нет. Новые сущности вроде `Invoice`, `BankRequest`, `EmailHistory` и `AuditLog`
можно добавлять как отдельные ORM-модели и отдельные explicit repositories без изменения текущего контракта.

## Поток инициализации

1. Composition root вызывает `build_storage_dependencies()`.
2. `Database` создаёт engine и `sessionmaker`.
3. `Database.initialize_schema()` создаёт ORM-таблицы через `Base.metadata.create_all(...)`.
4. `JsonToSQLiteMigrator.migrate()` один раз переносит legacy JSON.
5. Workflow получает готовые repository-абстракции и работает только через них.

## Session lifecycle

Каждый repository-метод открывает короткоживущую `Session`, выполняет одну операцию и закрывает её.
Commit/rollback управляется явно внутри infrastructure-слоя. В приложении и workflow `Session` не видна.

## Legacy JSON

Файлы `history.json` и `processed_messages.json` не удаляются автоматически.
Миграция безопасна и идемпотентна: повторный запуск не создаёт дубликаты и не повторяет уже отмеченные шаги.

## TODO

При появлении нескольких версий схемы заменить `create_all` на Alembic migration chain.
