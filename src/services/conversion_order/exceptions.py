"""Исключения домена Transfer Request."""


class TransferRequestError(Exception):
    """Базовая ошибка подготовки Transfer Request."""


class TransferRequestGenerationError(TransferRequestError):
    """Ошибка входных данных или состояния для генерации Transfer Request."""
