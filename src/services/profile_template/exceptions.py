class ProfileTemplateError(Exception):
    """Базовая ошибка импорта профиля."""


class InvalidProfileTemplateFormatError(ProfileTemplateError):
    """Файл профиля имеет неподдерживаемый формат."""


class ProfileTemplateTooLargeError(ProfileTemplateError):
    """Файл профиля превышает допустимый размер."""


class InvalidProfileTemplateError(ProfileTemplateError):
    """Профиль не проходит структуру или валидацию полей."""
