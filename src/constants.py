"""Общие константы проекта: форматы, пути и текстовые сообщения."""

from pathlib import Path


class Format:
    """Поддерживаемые расширения файлов для шаблонов и артефактов."""

    PDF = "pdf"
    DOCX = "docx"
    PNG = "png"


class Dir:
    """Ключевые директории и файлы, вычисляемые от корня проекта."""

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    TEMPLATE_PATH = PROJECT_ROOT / "templates"
    OUTPUT_DIR = PROJECT_ROOT / "output"
    # invoice
    INVOICE_TEMPLATE = TEMPLATE_PATH / f"invoice_template.{Format.DOCX}"
    INVOICE_OUTPUT_DIR = OUTPUT_DIR / "invoices"
    # bank
    BANK_OUTPUT_DIR = OUTPUT_DIR / "bank"

    ATTACHMENTS = PROJECT_ROOT / "attachments"
    SIGNATURE_PATH = TEMPLATE_PATH / f"signature.{Format.PNG}"

    TRANSFER_REQUEST_TEMPLATE = TEMPLATE_PATH / f"transfer_request_template.{Format.DOCX}"
    TRANSFER_REQUEST_OUTPUT_DIR = OUTPUT_DIR / "transfer_request"
    STORAGE_DIR = PROJECT_ROOT / "src" / "storage"
    STORAGE_DB = STORAGE_DIR / "storage.sqlite3"
    STORAGE_HISTORY_JSON = STORAGE_DIR / "history.json"
    STORAGE_PROCESSED_MESSAGES_JSON = STORAGE_DIR / "processed_messages.json"


class TestData:
    """Пути к тестовым шаблонам и фикстурам."""

    RESOURCES_DIR = Dir.PROJECT_ROOT / "tests/resources"

    INVOICE_TEMPLATE_PATH = RESOURCES_DIR / f"test_invoice_template.{Format.DOCX}"
    TRANSFER_TEMPLATE_PATH = RESOURCES_DIR / f"test_transfer_request_template.{Format.DOCX}"
    BANK_TEMPLATE_PATH = RESOURCES_DIR / f"test_bank_template.{Format.PDF}"


class Message:
    """Сообщения, которые workflow отправляет в Telegram."""

    START = "⚡ Magic is starting 🤞"
    NO_NEW_BANK_EMAIL = "ℹ️ No new bank email found."
    EMAIL_FETCHING_COMPLETED = "✔️ Email fetching completed"
    BANK_PDF_FILLED = "✔️ Bank pdf filled"
    INVOICE_GENERATED = "✔️ Invoice generated!"
    TRANSACTION_REQUEST_GENERATED = "✔️ Transaction request generated!"

    BANK_RESPONSE = (
        "Dobar dan,\n\n"
        "U prilogu dostavljam dokumenta koja ste tražili.\n"
        "Takođe vas molim da odmah izvršite prenos sredstava sa računa u evrima na račun u dinarima.\n\n"
        "S poštovanjem,\n"
        "K."
    )
