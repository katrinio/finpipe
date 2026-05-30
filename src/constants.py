from pathlib import Path


class Format:
    PDF = "pdf"
    DOCX = "docx"
    PNG = "png"


class Common:
    TEMPLATE_PATH = Path("templates")
    OUTPUT_DIR = Path("output")


class Invoice:
    TEMPLATE_PATH = Common.TEMPLATE_PATH / f"invoice_template.{Format.DOCX}"
    OUTPUT_DIR = Common.OUTPUT_DIR / "invoices"


class Bank:
    ATTACHMENTS_DIR = Path("attachments")
    SIGNATURE_PATH = Common.TEMPLATE_PATH / f"signature.{Format.PNG}"
    OUTPUT_DIR = Path("output/bank")


class TransferRequest:
    TEMPLATE_PATH = Common.TEMPLATE_PATH / f"transfer_request_template.{Format.DOCX}"
    OUTPUT_DIR = Path("output/transfer_request")


class TestData:
    RESOURCES_DIR = Path("tests/resources")

    TEMPLATE_PATH = RESOURCES_DIR / f"test_convert_to_pdf.{Format.DOCX}"
