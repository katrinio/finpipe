"""ORM-сущность технической записи о миграции."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseStorage


class AppliedMigration(BaseStorage):
    """Техническая запись о применённой миграции данных."""

    __tablename__ = "applied_migrations"

    migration_name: Mapped[str] = mapped_column(String, primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )
