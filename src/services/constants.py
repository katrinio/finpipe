from pathlib import Path


class Invoice:
    TEMPLATE_PATH = Path("templates/invoice_template.docx")
    OUTPUT_DIR = Path("output/invoices")


class Bank:
    TEMPLATE_PATH = Path("attachments/invoice_template.docx")
    SIGNATURE_PATH = Path("templates/signature.png")
    OUTPUT_DIR = Path("output/bank")
