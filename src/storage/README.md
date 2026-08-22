# Storage layer

The storage layer contains SQLAlchemy models for company profiles, bank details, invoice and bank amounts, encrypted signatures, Telegram update checkpoints, and workflow state. Signature metadata and encrypted bytes are persisted in PostgreSQL so the working encrypted file can be restored after a container replacement.

`initialize_storage()` binds active ORM models. Alembic migrations are applied explicitly before application startup; production deploy performs this with a one-shot Compose command.
