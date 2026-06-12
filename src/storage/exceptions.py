"""Исключения storage-слоя."""


class StorageError(Exception):
    """Базовая ошибка persistence-слоя."""


class StorageConfigurationError(StorageError):
    """Хранилище сконфигурировано некорректно."""


class StorageRecordNotFoundError(StorageError):
    """Ожидаемая запись в хранилище не найдена."""
