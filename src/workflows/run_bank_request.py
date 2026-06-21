"""Основной workflow обработки письма банка и подготовки документов."""

import logging
from dataclasses import dataclass
from pathlib import Path

from src.constants import Message
from src.integrations.gmail.gmail_models import BankEmail
from src.integrations.gmail.gmail_sender import send_reply
from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.services.bank.bank_extract import extract_amount
from src.services.monitoring.event_logger import EventLogger
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import AllowedUser, UserConfig
from src.storage.orm.system.app_events import EventSeverity, EventType
from src.storage.orm.user.bank_details import BankDetails
from src.utils.credentials import EnvVar
from src.utils.files import delete_file
from src.workflows.tasks.fetch_bank_email import fetch_bank_email_workflow
from src.workflows.tasks.generate_bank_confirmation import generate_bank_confirmation
from src.workflows.tasks.generate_conversion_order import generate_conversion_order_pdf
from src.workflows.tasks.generate_invoice import generate_invoice_pdf

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class BankDocuments:
    """Пути к документам, сгенерированным в рамках bank flow."""

    invoice_pdf: Path
    bank_confirmation: Path
    conversion_order: Path


def main() -> int:
    """Точка входа: инициализация и запуск bank flow."""

    configure_logging()
    EnvVar.get_dotenv()
    build_storage_dependencies()
    telegram_client = TelegramClient()
    owner = AllowedUser.get_owner()
    if owner is None:
        raise RuntimeError("Owner is not bootstrapped in storage")
    return run_bank_flow(telegram_client, owner.telegram_id)


def run_bank_flow(telegram_client: TelegramClient, telegram_id: int) -> int:
    """Запускает полный bank flow для указанного пользователя."""

    telegram_client.send_message(telegram_id, Message.START)

    try:
        fetch_result = fetch_bank_email_workflow(telegram_id=telegram_id)
    except RuntimeError as error:
        LOGGER.warning("Bank email workflow stopped: %s", error)
        telegram_client.send_message(telegram_id, Message.BANK_EMAIL_SEARCH_NOT_CONFIGURED)
        return 1

    if fetch_result is None:
        telegram_client.send_message(telegram_id, Message.NO_NEW_BANK_EMAIL)
        return 0

    bank_template_path, bank_email = fetch_result
    telegram_client.send_message(telegram_id, Message.EMAIL_FETCHING_COMPLETED)

    docs: BankDocuments | None = None
    try:
        docs = _generate_documents(telegram_client, telegram_id, bank_template_path)
        send_bank_response(telegram_client, telegram_id, docs.invoice_pdf, docs.conversion_order, docs.bank_confirmation)
        send_bank_email_reply(telegram_id=telegram_id, bank_email=bank_email, docs=docs)
    finally:
        _cleanup(bank_template_path, docs)

    return 0


def _generate_documents(
    telegram_client: TelegramClient,
    telegram_id: int,
    bank_template_path: Path,
) -> BankDocuments:
    """Генерирует три документа и отправляет статусные сообщения в Telegram."""

    received_amount_eur = extract_amount(bank_template_path)
    UserConfig.upsert(telegram_id=telegram_id, bank_received_amount_eur=received_amount_eur)
    EventLogger.log(
        EventType.SETTINGS_UPDATED,
        EventSeverity.INFO,
        {"telegram_id": telegram_id, "section": "user_config"},
    )

    user_config = UserConfig.get_by_owner(telegram_id)
    exchange_amount_eur = (
        user_config.conversion_amount_eur if user_config is not None and user_config.conversion_amount_eur is not None else received_amount_eur
    )
    invoice_amount_eur = user_config.invoice_amount_eur if user_config is not None else None

    bank_confirmation_path = generate_bank_confirmation(telegram_id, bank_template_path, amount=received_amount_eur)
    telegram_client.send_message(telegram_id, Message.BANK_CONFIRMATION_GENERATED)

    conversion_order_pdf_path = generate_conversion_order_pdf(
        telegram_id,
        invoice_amount_eur=invoice_amount_eur,
        bank_received_amount_eur=received_amount_eur,
        conversion_amount_eur=exchange_amount_eur,
    )
    telegram_client.send_message(telegram_id, Message.CONVERSION_ORDER_GENERATED)

    invoice_pdf_path = generate_invoice_pdf(telegram_id=telegram_id)
    telegram_client.send_message(telegram_id, Message.SALARY_INVOICE_GENERATED)

    return BankDocuments(
        invoice_pdf=invoice_pdf_path,
        bank_confirmation=bank_confirmation_path,
        conversion_order=conversion_order_pdf_path,
    )


def _cleanup(bank_template_path: Path, docs: BankDocuments | None) -> None:
    """Удаляет все временные файлы после завершения workflow."""

    delete_file(bank_template_path, LOGGER)
    if docs is None:
        return
    delete_file(docs.invoice_pdf, LOGGER)
    delete_file(docs.invoice_pdf.with_suffix(".docx"), LOGGER)
    delete_file(docs.bank_confirmation, LOGGER)
    delete_file(docs.conversion_order, LOGGER)
    delete_file(docs.conversion_order.with_suffix(".docx"), LOGGER)


def send_bank_response(telegram_client: TelegramClient, chat_id: int, *document_paths: Path) -> None:
    """Отправляет итоговые документы в Telegram."""

    telegram_client.send_message(chat_id, Message.BANK_RESPONSE)
    for document_path in document_paths:
        telegram_client.send_document(chat_id, document_path=document_path)


def send_bank_email_reply(
    telegram_id: int,
    bank_email: BankEmail,
    docs: BankDocuments,
) -> None:
    """Отправляет ответ на письмо банка с тремя документами в том же треде."""

    bank_details = BankDetails.get_by_owner(telegram_id)
    account_holder = bank_details.account_holder.title() if bank_details else ""
    account_holder_email = bank_details.account_holder_email or "" if bank_details else ""

    body = (
        f"Dobar dan,\n\n"
        f"U prilogu dostavljam dokumenta koja ste tražili.\n\n"
        f"Takođe vas molim da odmah izvršite prenos sredstava sa računa u evrima na račun u dinarima.\n\n"
        f"S poštovanjem,\n"
        f"{account_holder}\n"
        f"{account_holder_email}"
    )

    to_email = EnvVar.get_optional_env("EMAIL_DRY_RUN_RECIPIENT", bank_email.sender)

    send_reply(
        telegram_id=telegram_id,
        thread_id=bank_email.thread_id,
        to_email=to_email,
        cc=bank_email.cc,
        subject=f"Re: {bank_email.subject}",
        body=body,
        attachments=[docs.invoice_pdf, docs.bank_confirmation, docs.conversion_order],
    )


if __name__ == "__main__":
    raise SystemExit(main())
