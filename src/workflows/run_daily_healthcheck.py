"""Workflow отправки ежедневного healthcheck-отчёта в Telegram."""

import os

from scripts.bootstrap_allowed_users import bootstrap_primary_admin
from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import AllowedUser, DocumentGenerationHistory, DocumentType, GmailAccount, Signature
from src.utils.credentials import LOGGER, EnvVar


def main() -> int:
    """Собирает статусы из окружения и отправляет сводный отчёт."""

    configure_logging()

    try:
        build_storage_dependencies()
        bootstrap_primary_admin()
        owner_telegram_id = EnvVar.get_required_env("BOT_OWNER_TELEGRAM_ID")
        active_signatures_count = Signature.count()
        allowed_users_count = AllowedUser.count()
        # TODO: для доков сделать мониторинг за сутки
        generated_invoice_count = DocumentGenerationHistory.count(DocumentType.SALARY_INVOICE)
        generated_bank_pdf = DocumentGenerationHistory.count(DocumentType.BANK_CONFIRMATION)
        google_account_connected_count = GmailAccount.count()

        TelegramClient().send_daily_report(
            int(owner_telegram_id),
            unit_status=os.environ["UNIT_STATUS"],
            integration_status=os.environ["INTEGRATION_STATUS"],
            telegram_status=os.environ["TELEGRAM_STATUS"],
            duration_seconds=int(os.environ["DURATION"]),
            allowed_users_count=allowed_users_count,
            active_signatures_count=active_signatures_count,
            generated_invoice_count=generated_invoice_count,
            generated_bank_pdf=generated_bank_pdf,
            google_account_connected_count=google_account_connected_count,
        )
    except Exception:
        LOGGER.exception("Healthcheck failed.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
