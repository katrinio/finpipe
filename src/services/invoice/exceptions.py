"""Исключения домена Invoice."""


class InvoiceError(Exception):
    """Базовая ошибка генерации и подготовки Invoice."""


class InvoiceGenerationError(InvoiceError):
    """Ошибка входных данных или состояния для генерации Invoice."""
