"""Поиск последнего подходящего письма банка в Gmail."""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

from src.storage.orm.user.bank_details import BankDetails
from src.utils.credentials import EnvVar

from .gmail_models import BankEmail

LOGGER = logging.getLogger(__name__)
USER_ID = "me"
METADATA_HEADERS = ("Subject", "From", "Date", "Cc")


def _current_month_start() -> str:
    """Возвращает первый день текущего месяца в формате Gmail after:YYYY/MM/DD."""
    today = date.today()
    return f"{today.year}/{today.month:02d}/01"


@dataclass(frozen=True)
class BankEmailSearchConfig:
    """Настройки поиска письма банка."""

    sender: str
    recipient: str
    subject_contains: str
    source: str


def find_bank_email(service: Any, owner_telegram_id: int | None = None) -> BankEmail | None:
    """Находит самое новое письмо банка в пределах окна поиска."""

    config = load_bank_email_search_config(owner_telegram_id)
    LOGGER.info("Searching Gmail for bank email since %s", _current_month_start())
    LOGGER.info(
        "Searching bank confirmation email: sender=%s recipient=%s subject_contains=%s",
        mask_email(config.sender),
        mask_email(config.recipient),
        mask_text(config.subject_contains),
    )

    response = service.users().messages().list(userId=USER_ID, q=build_bank_email_query(config), maxResults=10).execute()
    messages = response.get("messages", [])
    if not messages:
        LOGGER.info("No Gmail messages matched the configured bank email filters")
        return None

    LOGGER.info("Found %s matching Gmail messages", len(messages))
    newest_message = max(
        (fetch_message_metadata(service, message["id"]) for message in messages),
        key=lambda message: int(message.get("internalDate", "0")),
    )

    bank_email = build_bank_email_result(newest_message)
    LOGGER.info(
        "Selected newest bank email: message_id=%s date=%s",
        bank_email.message_id,
        bank_email.date,
    )
    return bank_email


def load_bank_email_search_config(owner_telegram_id: int | None = None) -> BankEmailSearchConfig:
    """Загружает настройки поиска из профиля, а при отсутствии - из env fallback.

    Legacy/dev fallback нужен только для локального режима и старых установок.
    """

    if owner_telegram_id is not None:
        bank_details = BankDetails.get_by_owner(owner_telegram_id)
        if bank_details is not None:
            from src.services.bank.bank_config import get_bank_config

            bank_config = get_bank_config(bank_details.bank_slug)
            sender = bank_config.confirmation_email_sender if bank_config else None
            recipient = bank_details.bank_confirmation_email_recipient
            subject_contains = bank_details.bank_confirmation_email_subject_contains
            if sender and recipient and subject_contains:
                LOGGER.info("Bank confirmation email search config loaded from profile (bank_slug=%s)", bank_details.bank_slug)
                return BankEmailSearchConfig(sender=sender, recipient=recipient, subject_contains=subject_contains, source="profile")

    sender = EnvVar.get_optional_env("BANK_EMAIL_FROM", "")
    recipient = EnvVar.get_optional_env("BANK_EMAIL_TO", "")
    subject_contains = EnvVar.get_optional_env("BANK_EMAIL_SUBJECT", "")
    if sender and recipient and subject_contains:
        LOGGER.warning("Bank confirmation email search config loaded from env fallback")
        return BankEmailSearchConfig(sender=sender, recipient=recipient, subject_contains=subject_contains, source="env")

    raise RuntimeError(
        "Bank confirmation email search settings are missing. Fill bank_confirmation_email.sender, "
        "bank_confirmation_email.recipient and bank_confirmation_email.subject_contains in the profile, or set "
        "BANK_EMAIL_FROM, BANK_EMAIL_TO and BANK_EMAIL_SUBJECT for local fallback."
    )


def build_bank_email_query(config: BankEmailSearchConfig) -> str:
    """Собирает Gmail query из конфигурации поиска."""

    subject = config.subject_contains.replace('"', r"\"")
    sender = config.sender.replace('"', r"\"")
    recipient = config.recipient.replace('"', r"\"")
    return f'subject:"{subject}" from:"{sender}" to:"{recipient}" after:{_current_month_start()} has:attachment'


def mask_email(value: str) -> str:
    """Маскирует email для логов."""

    if "@" not in value:
        return value
    local, domain = value.split("@", 1)
    masked_local = "*" if not local else local[0] + "***"
    return f"{masked_local}@{domain}"


def mask_text(value: str) -> str:
    """Маскирует произвольный текст для логов."""

    if not value:
        return value
    return "..."


def fetch_message_metadata(service: Any, message_id: str) -> dict[str, Any]:
    """Читает только метаданные письма, без загрузки тела и вложений."""

    return (
        service.users()
        .messages()
        .get(
            userId=USER_ID,
            id=message_id,
            format="metadata",
            metadataHeaders=list(METADATA_HEADERS),
        )
        .execute()
    )


def build_bank_email_result(message: dict[str, Any]) -> BankEmail:
    """Преобразует Gmail API-ответ в внутреннюю модель письма."""

    headers = extract_headers(message)
    return BankEmail(
        subject=headers.get("subject", ""),
        sender=headers.get("from", ""),
        date=headers.get("date", ""),
        message_id=message["id"],
        thread_id=message["threadId"],
        cc=headers.get("cc", ""),
    )


def extract_headers(message: dict[str, Any]) -> dict[str, str]:
    """Извлекает заголовки письма в нормализованный словарь."""

    return {header.get("name", "").lower(): header.get("value", "") for header in message.get("payload", {}).get("headers", []) if header.get("name")}
