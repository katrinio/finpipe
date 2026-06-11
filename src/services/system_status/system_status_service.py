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
        bank_details = BankDetails.exists(telegram_id)
        signature = Signature.exists(telegram_id)
        gmail = GmailAccount.exists(telegram_id)

        return SystemStatus(
            company=company,
            bank_details=bank_details,
            signature=signature,
            gmail=gmail,
            bank_pdf_available=company and bank_details,
            invoice_available=company and bank_details and signature,
            transfer_request_available=company and bank_details,
        )
