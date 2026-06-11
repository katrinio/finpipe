"""Загрузка пользовательской подписи в encrypted storage и БД."""

import yaml

from src.services.profile_template.exceptions import InvalidProfileTemplateError
from src.services.profile_template.profile_template import ProfileTemplate
from src.services.profile_template.profile_template_validator import ProfileTemplateValidator
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.utils import Utils


class ProfileTemplateService:
    """Сервис загрузки пользовательской подписи."""

    REQUIRED_PROFILE_FIELDS = (
        "company_name",
        "company_address",
        "account_holder",
        "account_number",
        "iban",
        "bic",
        "bank_name",
    )

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

        profile = cls.parse(file_bytes)
        cls.validate_required_fields(profile)
        cls.import_profile(telegram_id, profile)

    @classmethod
    def parse(cls, file_bytes: bytes) -> ProfileTemplate:
        """Преобразует YAML bytes в ProfileTemplate."""

        data = yaml.safe_load(file_bytes.decode("utf-8"))
        profile_data: dict[str, str | None] = {
            "company_name": None,
            "company_address": None,
            "registration_number": None,
            "city": None,
            "account_holder": None,
            "account_holder_email": None,
            "account_holder_address": None,
            "bank_name": None,
            "account_number": None,
            "iban": None,
            "bic": None,
            "service_agreement_date": None,
            "payment_number": None,
            "payment_code": None,
            "payment_description": None,
        }
        if isinstance(data, dict):
            for key in profile_data:
                profile_data[key] = cls._normalize_profile_value(data.get(key), key)

        return ProfileTemplate(**profile_data)

    @classmethod
    def validate_required_fields(cls, profile: ProfileTemplate) -> None:
        """Проверяет, что профиль заполнен целиком по обязательным полям."""

        missing_fields = [field_name for field_name in cls.REQUIRED_PROFILE_FIELDS if cls._is_blank(getattr(profile, field_name))]
        if missing_fields:
            missing_fields_text = "\n".join(f"• {field_name}" for field_name in missing_fields)
            msg = (
                "❌ Профиль заполнен не полностью.\n"
                f"Не заполнены обязательные поля:\n{missing_fields_text}\n"
                "Исправьте шаблон и загрузите его повторно."
            )
            raise InvalidProfileTemplateError(msg)

    @staticmethod
    def _is_blank(value: str | None) -> bool:
        return value is None or not value.strip()

    @staticmethod
    def _normalize_profile_value(value: object, key: str) -> str | None:
        if value is None:
            return None

        if key == "service_agreement_date":
            return value if isinstance(value, str) else str(value)

        return value if isinstance(value, str) else str(value)

    @classmethod
    def parse_profile_template(cls, file_bytes: bytes) -> ProfileTemplate:
        """Backward-compatible alias for parse(...)."""

        return cls.parse(file_bytes)

    @classmethod
    def import_profile(cls, telegram_id: int, profile: ProfileTemplate) -> None:
        # TODO(HIGH):
        # Импорт сейчас делает полный upsert целиком.
        # Для re-import сценариев нужно перейти на обновление только изменённых значений,
        # чтобы не затирать пользовательские данные.
        CompanyProfile.upsert(
            owner_telegram_id=telegram_id,
            company_name=profile.company_name,
            company_address=profile.company_address,
            registration_number=profile.registration_number,
            city=profile.city,
            service_agreement_date=Utils.parse_iso_date(profile.service_agreement_date),
            payment_number=profile.payment_number,
            payment_code=profile.payment_code,
            payment_description=profile.payment_description,
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
