# Storage layer

The storage layer contains SQLAlchemy models for user access, profiles, bank details, invoice settings, encrypted signatures, Telegram updates and state, audit logs, monitoring events, and document-generation history.

`build_storage_dependencies()` upgrades the database to the current Alembic head and binds all active ORM models.
