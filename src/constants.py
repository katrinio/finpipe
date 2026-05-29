from pathlib import Path


class Format:
    PDF = "pdf"
    DOCX = "docx"
    PNG = "png"


class Invoice:
    TEMPLATE_PATH = Path(f"templates/invoice_template.{Format.DOCX}")
    OUTPUT_DIR = Path("output/invoices")


class Bank:
    ATTACHMENTS_DIR = Path("attachments")
    SIGNATURE_PATH = Path(f"templates/signature.{Format.PNG}")
    OUTPUT_DIR = Path("output/bank")
