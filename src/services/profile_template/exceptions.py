class ProfileTemplateError(Exception):
    """Базовая ошибка для подписи."""


class InvalidProfileTemplateFormatError(ProfileTemplateError):
    """Файл подписи имеет неподдерживаемый формат."""


class ProfileTemplateTooLargeError(ProfileTemplateError):
    """Файл подписи превышает допустимый размер."""


class InvalidProfileTemplateError(ProfileTemplateError):
    """Файл не может быть открыт как yaml."""
