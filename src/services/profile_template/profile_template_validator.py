"""Валидация пользовательской подписи перед сохранением."""

import yaml

from src.services.profile_template.exceptions import InvalidProfileTemplateError, InvalidProfileTemplateFormatError, ProfileTemplateTooLargeError


class ProfileTemplateValidator:
    """Проверяет подпись перед загрузкой и шифрованием."""

    MAX_SIZE_BYTES = 2 * 1024 * 1024

    @classmethod
    def validate_yaml(cls, file_name: str) -> None:
        """Разрешает только PNG-файлы."""

        if not file_name.lower().endswith(".yaml"):
            msg = f"ProfileTemplate file must be a YAML image: {file_name}"
            raise InvalidProfileTemplateFormatError(msg)

    @classmethod
    def validate_size(cls, file_size: int) -> None:
        """Проверяет, что размер подписи не превышает лимит."""

        if file_size > cls.MAX_SIZE_BYTES:
            msg = f"ProfileTemplate file is too large: {file_size} bytes"
            raise ProfileTemplateTooLargeError(msg)

    @classmethod
    def validate_yaml_structure(cls, file_bytes: bytes) -> None:
        """Проверяет, что файл содержит валидный YAML объект."""

        try:
            data = yaml.safe_load(file_bytes.decode("utf-8"))
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            msg = "Profile template is not a valid YAML file"
            raise InvalidProfileTemplateError(msg) from exc

        if not isinstance(data, dict):
            msg = "Profile template must contain a YAML object"
            raise InvalidProfileTemplateError(msg)

        if not data:
            msg = "Profile template is empty"
            raise InvalidProfileTemplateError(msg)
