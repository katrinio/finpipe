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

    CONVERSION_ORDER_TEMPLATE = TEMPLATE_PATH / f"conversion_order_template.{Format.DOCX}"
    CONVERSION_ORDER_OUTPUT_DIR = OUTPUT_DIR / "conversion_order"
    STORAGE_DIR = PROJECT_ROOT / "src" / "storage"
    SIGNATURE_ENC = STORAGE_DIR / "signatures" / "signature.enc"
    PROFILE_TEMPLATE = TEMPLATE_PATH / "profile_template.yaml"


class TestData:
    """Пути к тестовым шаблонам и фикстурам."""

    RESOURCES_DIR = Dir.PROJECT_ROOT / "tests/resources"

    INVOICE_TEMPLATE_PATH = RESOURCES_DIR / f"test_invoice_template.{Format.DOCX}"
    CONVERSION_ORDER_TEMPLATE_PATH = RESOURCES_DIR / f"test_conversion_order_template.{Format.DOCX}"
    BANK_TEMPLATE_PATH = RESOURCES_DIR / f"test_bank_template.{Format.PDF}"
