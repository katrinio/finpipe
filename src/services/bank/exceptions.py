"""Исключения домена банковских PDF и bank workflow."""


class BankPdfError(Exception):
    """Базовая ошибка подготовки банковского PDF."""


class BankPdfValidationError(BankPdfError):
    """Ошибка входных данных или исходного PDF банка."""


class BankAmountExtractionError(BankPdfError):
    """Не удалось извлечь сумму из PDF банка."""
