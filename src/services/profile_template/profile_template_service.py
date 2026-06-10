"""Загрузка пользовательской подписи в encrypted storage и БД."""

from __future__ import annotations

import yaml

from src.services.profile_template.profile_template import ProfileTemplate
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

    @classmethod
    def parse_profile_template(cls, file_bytes: bytes) -> ProfileTemplate:
        data = yaml.safe_load(file_bytes)
        print(data)

        return ProfileTemplate(**data)

    @classmethod
    def import_profile(cls, telegram_id: int, profile: ProfileTemplate) -> ProfileTemplate:
        # CompanyProfile.upsert(...)
        #
        # BankDetails.upsert(...)
        ...
