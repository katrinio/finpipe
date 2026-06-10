"""Загрузка пользовательской подписи в encrypted storage и БД."""

from __future__ import annotations

import yaml

from src.services.profile_template.profile_template import ProfileTemplate
from src.services.profile_template.profile_template_validator import ProfileTemplateValidator
from src.storage.orm.bank_details import BankDetails
from src.storage.orm.company_profile import CompanyProfile


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
    def import_profile(cls, telegram_id: int, profile: ProfileTemplate) -> None:
        CompanyProfile.upsert(
            owner_telegram_id=telegram_id,
            company_name=profile.company_name,
            company_address=profile.company_address,
            account_holder=profile.account_holder,
        )

        BankDetails.upsert(
            owner_telegram_id=telegram_id,
            bank_name=profile.bank_name,
            iban=profile.iban,
            bic=profile.bic,
        )
