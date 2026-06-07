"""Базовый declarative class для ORM storage-слоя."""

from sqlalchemy.orm import DeclarativeBase


class BaseStorage(DeclarativeBase):
    """Общий SQLAlchemy base для всех storage-сущностей."""
