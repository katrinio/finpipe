# Storage layer

The storage layer contains SQLAlchemy models for profiles, bank details, document settings, encrypted signatures, Telegram updates, and workflow state.

`initialize_storage()` binds active ORM models. Alembic migrations are applied explicitly before application startup; production deploy performs this with a one-shot Compose command.
