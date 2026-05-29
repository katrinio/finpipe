import logging
import re
from pathlib import Path

from pypdf import PdfReader

LOGGER = logging.getLogger(__name__)
AMOUNT_PATTERN = re.compile(r"Iznos\s+EUR\s+([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2})")


def extract_amount(pdf_path: Path) -> float:
    text = extract_text(pdf_path)
    match = AMOUNT_PATTERN.search(text)
    if match is None:
        msg = f"Amount not found in PDF: {pdf_path}"
        raise ValueError(msg)

    amount_text = match.group(1).replace(",", "")
    amount = float(amount_text)
    LOGGER.info("Extracted amount %.2f from %s", amount, pdf_path)
    return amount


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
