"""Инициализация storage-слоя приложения."""

from src.storage.orm.database import Database


def initialize_storage() -> None:
    """Привязывает ORM-модели к настроенной базе данных."""

    database = Database.from_env()
    database.bind_models()
