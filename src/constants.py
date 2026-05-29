from pathlib import Path


class Format:
    PDF = "pdf"
    DOCX = "docx"
    PNG = "png"


class Invoice:
    TEMPLATE_PATH = Path(f"templates/invoice_template.{Format.DOCX}")
    OUTPUT_DIR = Path("output/invoices")


class Bank:
    TEMPLATE_PATH = Path(f"attachments/invoice_template.{Format.DOCX}")
    SIGNATURE_PATH = Path(f"templates/signature.{Format.PNG}")
    OUTPUT_DIR = Path("output/bank")
