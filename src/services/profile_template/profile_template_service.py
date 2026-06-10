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
    def parse(cls, file_bytes: bytes) -> ProfileTemplate:
        """Преобразует YAML bytes в ProfileTemplate."""

        data = yaml.safe_load(file_bytes.decode("utf-8"))
        profile_data = {
            "company_name": None,
            "company_address": None,
            "account_holder": None,
            "account_holder_email": None,
            "account_holder_address": None,
            "bank_name": None,
            "account_number": None,
            "iban": None,
            "bic": None,
            "service_agreement_date": None,
        }
        if isinstance(data, dict):
            for key in profile_data:
                profile_data[key] = data.get(key)

        return ProfileTemplate(**profile_data)

    @classmethod
    def parse_profile_template(cls, file_bytes: bytes) -> ProfileTemplate:
        """Backward-compatible alias for parse(...)."""

        return cls.parse(file_bytes)

    @classmethod
    def import_profile(cls, telegram_id: int, profile: ProfileTemplate) -> None:
        CompanyProfile.upsert(
            owner_telegram_id=telegram_id,
            company_name=profile.company_name,
            company_address=profile.company_address,
            service_agreement_date=profile.service_agreement_date,
        )

        BankDetails.upsert(
            owner_telegram_id=telegram_id,
            account_holder=profile.account_holder,
            account_holder_email=profile.account_holder_email,
            account_holder_address=profile.account_holder_address,
            amount=None,
            bank_name=profile.bank_name,
            account_number=profile.account_number,
            iban=profile.iban,
            bic=profile.bic,
        )
