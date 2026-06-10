"""Загрузка пользовательской подписи в encrypted storage и БД."""

from __future__ import annotations

from src.services.profile_template.profile_template_validator import ProfileTemplateValidator


class ProfileTemplateService:
    """Сервис загрузки пользовательской подписи."""

    @classmethod
    def upload(
        cls,
        telegram_id: int,
        file_name: str,
        file_size: int,
        file_bytes: bytes,
    ) -> None:

        ProfileTemplateValidator.validate_yaml(file_name)
        ProfileTemplateValidator.validate_size(file_size)
        ProfileTemplateValidator.validate_yaml_structure(file_bytes)
