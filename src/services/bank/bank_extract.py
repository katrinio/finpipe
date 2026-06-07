"""Извлечение суммы из PDF-уведомления банка."""

import logging
import re
from pathlib import Path

from pypdf import PdfReader

LOGGER = logging.getLogger(__name__)
AMOUNT_PATTERN = re.compile(r"Iznos\s+EUR\s+([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2})")


def extract_amount(pdf_path: Path) -> float:
    """Читает PDF банка и возвращает найденную сумму в EUR."""

    LOGGER.info("Extracting amount from bank PDF: %s", pdf_path)
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
    """Извлекает текст со всех страниц PDF."""

    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
