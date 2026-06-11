"""Исключения для операций с пользовательской подписью."""


class SignatureError(Exception):
    """Базовая ошибка для подписи."""


class InvalidSignatureFormatError(SignatureError):
    """Файл подписи имеет неподдерживаемый формат."""


class SignatureTooLargeError(SignatureError):
    """Файл подписи превышает допустимый размер."""


class InvalidSignatureImageError(SignatureError):
    """Файл не может быть открыт как изображение."""
