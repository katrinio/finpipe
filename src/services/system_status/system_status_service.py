"""Сборка сводного статуса профиля и документных зависимостей."""

from src.services.system_status.system_status import SystemStatus
from src.storage.orm import Signature
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.storage.orm.user.gmail_account import GmailAccount


class SystemStatusService:
    """Собирает признаки готовности профиля и документов."""

    @classmethod
    def get_status(cls, telegram_id: int) -> SystemStatus:
        """Возвращает готовность профиля, интеграций и документов пользователя."""

        company = CompanyProfile.exists(telegram_id)
        bd = BankDetails.get_by_owner(telegram_id)
        bank_details = bd is not None
        signature = Signature.exists(telegram_id)
        gmail = GmailAccount.has_gmail_connection(telegram_id)

        from src.services.bank.bank_config import get_bank_config

        bank_config = get_bank_config(bd.bank_slug if bd else None)
        bank_email_configured = (
            bd is not None
            and bank_config is not None
            and bool(bd.bank_confirmation_email_recipient and bd.bank_confirmation_email_recipient.strip())
            and bool(bd.bank_confirmation_email_subject_contains and bd.bank_confirmation_email_subject_contains.strip())
        )

        return SystemStatus(
            company=company,
            bank_details=bank_details,
            signature=signature,
            gmail=gmail,
            bank_email_configured=bank_email_configured,
            bank_confirmation_available=company and bank_details,
            invoice_available=company and bank_details and signature,
            conversion_order_available=company and bank_details,
        )
