from __future__ import annotations


class ProfileTemplateError(Exception):
    """Базовая ошибка для подписи."""


class InvalidProfileTemplateFormatError(ProfileTemplateError):
    """Файл подписи имеет неподдерживаемый формат."""


class ProfileTemplateTooLargeError(ProfileTemplateError):
    """Файл подписи превышает допустимый размер."""


class InvalidProfileTemplateImageError(ProfileTemplateError):
    """Файл не может быть открыт как изображение."""
