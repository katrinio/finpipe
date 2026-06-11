from collections.abc import Mapping

from src.constants import Dir
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.messages import BotInfo
from src.services.profile_template.exceptions import InvalidProfileTemplateError, InvalidProfileTemplateFormatError, ProfileTemplateTooLargeError
from src.services.profile_template.profile_template_service import ProfileTemplateService
from src.storage.orm import Signature, UserConfig
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile


class ProfileHandlers:
    def __init__(self, telegram: TelegramClient, state_service: UserStateService) -> None:
        self.telegram = telegram
        self.state_service = state_service

    def handle_profile_template_upload(self, telegram_id: int, file_name: str, file_size: int, file_bytes: bytes) -> None:
        try:
            ProfileTemplateService.upload(
                telegram_id=telegram_id,
                file_name=file_name,
                file_size=file_size,
                file_bytes=file_bytes,
            )
        except InvalidProfileTemplateFormatError:
            self.telegram.send_message(telegram_id, BotInfo.PROFILE_TEMPLATE_NOT_YAML)
            return
        except ProfileTemplateTooLargeError:
            self.telegram.send_message(telegram_id, BotInfo.PROFILE_TEMPLATE_TOO_LARGE)
            return
        except InvalidProfileTemplateError as error:
            self.telegram.send_message(telegram_id, str(error))
            return

        self.state_service.clear_state(telegram_id)
        company_profile = CompanyProfile.get_by_owner(telegram_id)
        bank_details = BankDetails.get_by_owner(telegram_id)
        if company_profile is None or bank_details is None:
            self.telegram.send_message(telegram_id, BotInfo.PROFILE_TEMPLATE_UPDATED)
            return

        self.telegram.send_message(
            telegram_id,
            (f"✅ Профиль успешно загружен.\nКомпания: {company_profile.company_name}\nБанк: {bank_details.bank_name}"),
        )

    def upload_template(self, telegram_id: int) -> None:
        self.state_service.set_state(telegram_id, UserState.WAITING_PROFILE_TEMPLATE_UPLOAD)
        self.telegram.send_message(telegram_id, BotInfo.PROFILE_TEMPLATE_REQUIREMENTS)

    def download_template(self, telegram_id: int) -> None:
        self.telegram.send_document(telegram_id, document_path=Dir.PROFILE_TEMPLATE)
        self.telegram.send_message(telegram_id, BotInfo.PROFILE_TEMPLATE_SENT)

    def show_profile(self, telegram_id: int) -> None:
        company_profile = CompanyProfile.get_by_owner(telegram_id)
        bank_details = BankDetails.get_by_owner(telegram_id)
        user_config = UserConfig.get_by_owner(telegram_id)
        signature = Signature.get_active(telegram_id)

        company_fields = {
            "company_name": company_profile.company_name if company_profile is not None else None,
            "company_address": company_profile.company_address if company_profile is not None else None,
            "registration_number": company_profile.registration_number if company_profile is not None else None,
            "city": company_profile.city if company_profile is not None else None,
        }
        bank_fields = {
            "account_holder": bank_details.account_holder if bank_details is not None else None,
            "account_number": bank_details.account_number if bank_details is not None else None,
            "iban": bank_details.iban if bank_details is not None else None,
            "bic": bank_details.bic if bank_details is not None else None,
            "bank_name": bank_details.bank_name if bank_details is not None else None,
        }
        payment_fields = {
            "payment_number": company_profile.payment_number if company_profile is not None else None,
            "payment_code": company_profile.payment_code if company_profile is not None else None,
            "payment_description": company_profile.payment_description if company_profile is not None else None,
        }

        company_status = self.get_section_status(company_fields)
        bank_status = self.get_section_status(bank_fields)
        payment_status = self.get_section_status(payment_fields)
        signature_status = self.get_binary_status(signature is not None)
        invoice_status = self.get_binary_status(user_config is not None and user_config.invoice_amount is not None)

        missing_fields = (
            self.collect_missing_fields(company_fields) + self.collect_missing_fields(bank_fields) + self.collect_missing_fields(payment_fields)
        )

        profile_parts = [
            "👤 Профиль",
            "",
            f"🏢 Компания         {company_status}",
            f"🏦 Реквизиты        {bank_status}",
            f"💳 Платёж           {payment_status}",
            f"✍️ Подпись          {signature_status}",
            f"💰 Invoice          {invoice_status}",
        ]

        if missing_fields:
            profile_parts.extend(
                [
                    "",
                    "Не заполнено:",
                    *(f"• {field_name}" for field_name in missing_fields),
                ]
            )

        profile_parts.extend(
            [
                "",
                "🏢 Компания",
                f"• {self.format_field(company_fields['company_name'])}",
                f"• {self.format_field(company_fields['company_address'])}",
                f"• Регистрационный номер: {self.format_field(company_fields['registration_number'])}",
                f"• Город: {self.format_field(company_fields['city'])}",
                "",
                "🏦 Банковские реквизиты",
                f"• Банк: {self.format_field(bank_fields['bank_name'])}",
                f"• Получатель: {self.format_field(bank_fields['account_holder'])}",
                f"• Счёт: {self.format_field(bank_fields['account_number'])}",
                f"• IBAN: {self.format_field(bank_fields['iban'])}",
                f"• BIC: {self.format_field(bank_fields['bic'])}",
                "",
                "💳 Платёж",
                f"• Номер платежа: {self.format_field(payment_fields['payment_number'])}",
                f"• Код платежа: {self.format_field(payment_fields['payment_code'])}",
                f"• Описание платежа: {self.format_field(payment_fields['payment_description'])}",
                "",
                "✍️ Подпись",
                f"• {self.format_signature_state(signature is not None)}",
                "",
                "💰 Invoice",
                f"• {self.format_invoice_amount(user_config.invoice_amount if user_config is not None else None)}",
            ]
        )

        self.telegram.send_message(telegram_id, "\n".join(profile_parts))

    @staticmethod
    def get_section_status(fields: Mapping[str, object | None]) -> str:
        filled_count = sum(1 for value in fields.values() if ProfileHandlers.is_present(value))
        if filled_count == 0:
            return "⭕"
        if filled_count == len(fields):
            return "✔️"
        return "➖"

    @staticmethod
    def get_binary_status(is_ready: bool) -> str:
        return "✔️" if is_ready else "⭕"

    @staticmethod
    def collect_missing_fields(fields: Mapping[str, object | None]) -> list[str]:
        return [field_name for field_name, value in fields.items() if not ProfileHandlers.is_present(value)]

    @staticmethod
    def is_present(value: object | None) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        return True

    @staticmethod
    def format_field(value: object | None) -> str:
        return str(value) if ProfileHandlers.is_present(value) else "—"

    @staticmethod
    def format_invoice_amount(value: int | None) -> str:
        return f"{value} EUR" if value is not None else "—"

    @staticmethod
    def format_signature_state(is_loaded: bool) -> str:
        return "Загружена" if is_loaded else "Не загружена"
