"""Импорт профиля пользователя из YAML в ORM."""

import logging
from datetime import datetime, time

import yaml
from sqlalchemy import select

from src.services.monitoring.event_logger import EventLogger
from src.services.profile_template.exceptions import InvalidProfileTemplateError
from src.services.profile_template.profile_template import BankConfirmationEmailTemplate, ProfileTemplate
from src.services.profile_template.profile_template_validator import ProfileTemplateValidator
from src.storage.orm.system.app_events import EventSeverity, EventType
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.utils.utils import Utils

LOGGER = logging.getLogger(__name__)


class ProfileTemplateService:
    """Импортирует и валидирует профиль пользователя."""

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
        """Проверяет YAML-шаблон и сохраняет профиль пользователя."""

        LOGGER.info("Validating profile template for Telegram user %s", telegram_id)
        ProfileTemplateValidator.validate_yaml(file_name)
        ProfileTemplateValidator.validate_size(file_size)
        ProfileTemplateValidator.validate_yaml_structure(file_bytes)

        profile = cls.parse(file_bytes)
        cls.validate_required_fields(profile)
        cls.import_profile(telegram_id, profile)
        LOGGER.info("Profile template persisted for Telegram user %s", telegram_id)

    @classmethod
    def parse(cls, file_bytes: bytes) -> ProfileTemplate:
        """Преобразует YAML в объект профиля."""

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
        bank_confirmation_email = BankConfirmationEmailTemplate(sender=None, recipient=None, subject_contains=None)
        if isinstance(data, dict):
            for key in profile_data:
                profile_data[key] = cls._normalize_profile_value(data.get(key), key)
            bank_confirmation_email = cls._parse_bank_confirmation_email(data.get("bank_confirmation_email"))

        return ProfileTemplate(**profile_data, bank_confirmation_email=bank_confirmation_email)

    @classmethod
    def validate_required_fields(cls, profile: ProfileTemplate) -> None:
        """Проверяет, что профиль заполнен целиком по обязательным полям."""

        missing_fields = [field_name for field_name in cls.REQUIRED_PROFILE_FIELDS if cls._is_blank(getattr(profile, field_name))]
        if missing_fields:
            LOGGER.warning("Profile template missing required fields for Telegram user input")
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

    @staticmethod
    def _parse_bank_confirmation_email(value: object) -> BankConfirmationEmailTemplate:
        if not isinstance(value, dict):
            return BankConfirmationEmailTemplate(sender=None, recipient=None, subject_contains=None)

        return BankConfirmationEmailTemplate(
            sender=ProfileTemplateService._normalize_profile_value(value.get("sender"), "sender"),
            recipient=ProfileTemplateService._normalize_profile_value(value.get("recipient"), "recipient"),
            # Тема письма может содержать дату, номер или сумму, поэтому используем contains-match.
            subject_contains=ProfileTemplateService._normalize_profile_value(value.get("subject_contains"), "subject_contains"),
        )

    @classmethod
    def import_profile(cls, telegram_id: int, profile: ProfileTemplate) -> None:
        """Сохраняет профиль компании и банковские реквизиты пользователя."""

        # TODO(HIGH):
        # Импорт сейчас делает полный upsert целиком.
        # Для re-import сценариев нужно перейти на обновление только изменённых значений,
        # чтобы не затирать пользовательские данные.
        with CompanyProfile.session() as session:
            company_profile = session.scalar(select(CompanyProfile).where(CompanyProfile.owner_telegram_id == telegram_id).limit(1))
            if company_profile is None:
                company_profile = CompanyProfile(
                    owner_telegram_id=telegram_id,
                    company_name=cls._require_text(profile.company_name),
                    company_address=cls._require_text(profile.company_address),
                    registration_number=profile.registration_number,
                    city=profile.city,
                    service_agreement_date=cls._require_datetime(profile.service_agreement_date),
                    payment_number=profile.payment_number,
                    payment_code=profile.payment_code,
                    payment_description=profile.payment_description,
                    bank_confirmation_email_sender=profile.bank_confirmation_email.sender,
                    bank_confirmation_email_recipient=profile.bank_confirmation_email.recipient,
                    bank_confirmation_email_subject_contains=profile.bank_confirmation_email.subject_contains,
                )
                session.add(company_profile)
            else:
                company_profile.company_name = cls._require_text(profile.company_name)
                company_profile.company_address = cls._require_text(profile.company_address)
                company_profile.registration_number = profile.registration_number
                company_profile.city = profile.city
                company_profile.service_agreement_date = cls._require_datetime(profile.service_agreement_date)
                company_profile.payment_number = profile.payment_number
                company_profile.payment_code = profile.payment_code
                company_profile.payment_description = profile.payment_description

            bank_details = session.scalar(select(BankDetails).where(BankDetails.owner_telegram_id == telegram_id).limit(1))
            if bank_details is None:
                bank_details = BankDetails(
                    owner_telegram_id=telegram_id,
                    account_holder=cls._require_text(profile.account_holder),
                    account_holder_email=profile.account_holder_email,
                    account_holder_address=profile.account_holder_address,
                    amount=None,
                    bank_name=cls._require_text(profile.bank_name),
                    account_number=cls._require_text(profile.account_number),
                    iban=cls._require_text(profile.iban),
                    bic=cls._require_text(profile.bic),
                    bank_confirmation_email_sender=profile.bank_confirmation_email.sender,
                    bank_confirmation_email_recipient=profile.bank_confirmation_email.recipient,
                    bank_confirmation_email_subject_contains=profile.bank_confirmation_email.subject_contains,
                )
                session.add(bank_details)
            else:
                bank_details.account_holder = cls._require_text(profile.account_holder)
                bank_details.account_holder_email = profile.account_holder_email
                bank_details.account_holder_address = profile.account_holder_address
                bank_details.amount = None
                bank_details.bank_name = cls._require_text(profile.bank_name)
                bank_details.account_number = cls._require_text(profile.account_number)
                bank_details.iban = cls._require_text(profile.iban)
                bank_details.bic = cls._require_text(profile.bic)
                bank_details.bank_confirmation_email_sender = profile.bank_confirmation_email.sender
                bank_details.bank_confirmation_email_recipient = profile.bank_confirmation_email.recipient
                bank_details.bank_confirmation_email_subject_contains = profile.bank_confirmation_email.subject_contains

            session.commit()
        EventLogger.log(
            EventType.SETTINGS_UPDATED,
            EventSeverity.INFO,
            {"telegram_id": telegram_id, "section": "bank_details"},
        )
        EventLogger.log(
            EventType.SETTINGS_UPDATED,
            EventSeverity.INFO,
            {"telegram_id": telegram_id, "section": "company_profile"},
        )
        LOGGER.info("Profile data imported for Telegram user %s", telegram_id)

    @staticmethod
    def _require_text(value: str | None) -> str:
        if value is None:
            msg = "Profile field is missing"
            raise InvalidProfileTemplateError(msg)
        return value

    @staticmethod
    def _require_datetime(value: str | None) -> datetime | None:
        if value is None:
            return None

        parsed_date = Utils.parse_iso_date(value)
        if parsed_date is None:
            return None
        return datetime.combine(parsed_date, time.min)
