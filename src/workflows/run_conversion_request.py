"""Workflow отправки запроса на конвертацию евро в динары."""

import logging
from pathlib import Path

from src.integrations.gmail.gmail_sender import send_email
from src.integrations.telegram.client import TelegramClient
from src.services.bank.bank_config import get_bank_config
from src.services.conversion_order.exceptions import TransferRequestError
from src.storage.orm.user.bank_details import BankDetails
from src.utils.credentials import EnvVar
from src.utils.files import delete_file
from src.workflows.tasks.generate_conversion_order import generate_conversion_order_pdf

LOGGER = logging.getLogger(__name__)

CONVERSION_REQUEST_SUBJECT = "Zahtev za konverziju deviza"


def send_conversion_request(telegram_client: TelegramClient, telegram_id: int, amount_eur: float) -> None:
    """Генерирует Conversion Order и отправляет запрос на конвертацию в банк."""

    bank_details = BankDetails.get_by_owner(telegram_id)
    if bank_details is None:
        msg = "Банковские реквизиты не настроены."
        raise TransferRequestError(msg)

    bank_config = get_bank_config(bank_details.bank_slug)
    if bank_config is None:
        msg = "Банк не настроен. Добавьте bank_slug в профиль."
        raise TransferRequestError(msg)

    account_holder = bank_details.account_holder.title() if bank_details.account_holder else ""
    account_holder_email = bank_details.account_holder_email or ""

    body = (
        f"Dobar dan,\n\n"
        f"Molim Vas da izvršite konverziju deviza sa mog deviznog računa u iznosu od {amount_eur:.2f} EUR.\n\n"
        f"U prilogu se nalazi zahtev za konverziju.\n\n"
        f"S poštovanjem,\n"
        f"{account_holder}\n"
        f"{account_holder_email}"
    )

    conversion_order_path: Path | None = None
    try:
        conversion_order_path = generate_conversion_order_pdf(
            telegram_id=telegram_id,
            conversion_amount_eur=amount_eur,
        )

        resolved_to = EnvVar.get_optional_env("EMAIL_DRY_RUN_RECIPIENT", bank_config.conversion_to)
        send_email(
            telegram_id=telegram_id,
            to_email=resolved_to,
            subject=CONVERSION_REQUEST_SUBJECT,
            body=body,
            attachments=[conversion_order_path],
            cc=bank_config.conversion_cc,
        )
        LOGGER.info("Conversion request sent for Telegram user %s, amount=%.2f EUR", telegram_id, amount_eur)
    finally:
        if conversion_order_path is not None:
            delete_file(conversion_order_path, LOGGER)
            delete_file(conversion_order_path.with_suffix(".docx"), LOGGER)
