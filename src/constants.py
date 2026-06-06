from pathlib import Path


class Format:
    PDF = "pdf"
    DOCX = "docx"
    PNG = "png"


class Dir:
    TEMPLATE_PATH = Path("templates")
    OUTPUT_DIR = Path("output")
    # invoice
    INVOICE_TEMPLATE = TEMPLATE_PATH / f"invoice_template.{Format.DOCX}"
    INVOICE_OUTPUT_DIR = OUTPUT_DIR / "invoices"
    # bank
    BANK_OUTPUT_DIR = OUTPUT_DIR / "bank"

    ATTACHMENTS = Path("attachments")
    SIGNATURE_PATH = TEMPLATE_PATH / f"signature.{Format.PNG}"

    TRANSFER_REQUEST_TEMPLATE = TEMPLATE_PATH / f"transfer_request_template.{Format.DOCX}"
    TRANSFER_REQUEST_OUTPUT_DIR = OUTPUT_DIR / "transfer_request"


class TestData:
    RESOURCES_DIR = Path("tests/resources")

    INVOICE_TEMPLATE_PATH = RESOURCES_DIR / f"test_invoice_template.{Format.DOCX}"
    TRANSFER_TEMPLATE_PATH = RESOURCES_DIR / f"test_transfer_request_template.{Format.DOCX}"
    BANK_TEMPLATE_PATH = RESOURCES_DIR / f"test_bank_template.{Format.PDF}"


class Message:
    BANK_RESPONSE = (
        "Dobar dan,\n\n",
        "U prilogu dostavljam dokumenta koja ste tražili.\n"
        "Takođe vas molim da odmah izvršite prenos sredstava sa računa u evrima na račun u dinarima.\n\n"
        "S poštovanjem,\n"
        "K.",
    )
