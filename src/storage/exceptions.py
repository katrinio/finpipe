"""Исключения storage-слоя."""


class StorageError(Exception):
    """Базовая ошибка persistence-слоя."""


class StorageRecordNotFoundError(StorageError):
    """Ожидаемая запись в хранилище не найдена."""
