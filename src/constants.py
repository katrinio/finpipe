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
    DATA_DIR = PROJECT_ROOT / "data"
    TEMPLATE_PATH = PROJECT_ROOT / "templates"
    OUTPUT_DIR = PROJECT_ROOT / "output"
    # invoice
    INVOICE_TEMPLATE = TEMPLATE_PATH / f"invoice_template.{Format.DOCX}"
    INVOICE_OUTPUT_DIR = OUTPUT_DIR / "invoices"
    # bank
    BANK_OUTPUT_DIR = OUTPUT_DIR / "bank"

    ATTACHMENTS = PROJECT_ROOT / "attachments"
    SIGNATURE_PATH = TEMPLATE_PATH / f"signature.{Format.PNG}"

    CONVERSION_ORDER_TEMPLATE = TEMPLATE_PATH / f"conversion_order_template.{Format.DOCX}"
    CONVERSION_ORDER_OUTPUT_DIR = OUTPUT_DIR / "conversion_order"
    STORAGE_DIR = PROJECT_ROOT / "src" / "storage"
    SIGNATURE_ENC = STORAGE_DIR / "signatures" / "signature.enc"
    STORAGE_DB = DATA_DIR / "finpipe.db"

    PROFILE_TEMPLATE = TEMPLATE_PATH / "profile_template.yaml"


class TestData:
    """Пути к тестовым шаблонам и фикстурам."""

    RESOURCES_DIR = Dir.PROJECT_ROOT / "tests/resources"

    INVOICE_TEMPLATE_PATH = RESOURCES_DIR / f"test_invoice_template.{Format.DOCX}"
    CONVERSION_ORDER_TEMPLATE_PATH = RESOURCES_DIR / f"test_conversion_order_template.{Format.DOCX}"
    BANK_TEMPLATE_PATH = RESOURCES_DIR / f"test_bank_template.{Format.PDF}"


class Message:
    """Сообщения, которые workflow отправляет в Telegram."""

    START = "⚡ Magic is starting 🤞"
    NO_NEW_BANK_EMAIL = "ℹ️ No new bank email found."
    BANK_EMAIL_SEARCH_NOT_CONFIGURED = (
        "⚠️ Bank email search settings are missing.\n"
        "Fill bank_confirmation_email.sender, bank_confirmation_email.recipient and bank_confirmation_email.subject_contains in the profile."
    )
    EMAIL_FETCHING_COMPLETED = "✔️ Email fetching completed"
    BANK_CONFIRMATION_GENERATED = "✔️ Bank confirmation generated!"
    SALARY_INVOICE_GENERATED = "✔️ Salary invoice generated!"
    CONVERSION_ORDER_GENERATED = "✔️ Conversion order generated!"

    BANK_RESPONSE = (
        "Dobar dan,\n\n"
        "U prilogu dostavljam dokumenta koja ste tražili.\n"
        "Takođe vas molim da odmah izvršite prenos sredstava sa računa u evrima na račun u dinarima.\n\n"
        "S poštovanjem,\n"
        "K."
    )
