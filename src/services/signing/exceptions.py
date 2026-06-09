"""Исключения для операций с пользовательской подписью."""

from __future__ import annotations


class SignatureError(Exception):
    """Базовая ошибка для подписи."""


class InvalidSignatureFormatError(SignatureError):
    """Файл подписи имеет неподдерживаемый формат."""


class SignatureTooLargeError(SignatureError):
    """Файл подписи превышает допустимый размер."""


class InvalidSignatureImageError(SignatureError):
    """Файл не может быть открыт как изображение."""
