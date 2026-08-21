"""Сборка сводного статуса профиля и документных зависимостей."""

from src.services.system_status.system_status import SystemStatus
from src.storage.orm import Signature
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile


class SystemStatusService:
    """Собирает признаки готовности профиля и документов."""

    @classmethod
    def get_status(cls, telegram_id: int) -> SystemStatus:
        """Возвращает готовность профиля, интеграций и документов пользователя."""

        company = CompanyProfile.exists(telegram_id)
        bd = BankDetails.get_by_owner(telegram_id)
        bank_details = bd is not None
        signature = Signature.exists(telegram_id)
        return SystemStatus(
            company=company,
            bank_details=bank_details,
            signature=signature,
            invoice_available=company and bank_details and signature,
        )
