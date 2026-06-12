from pathlib import Path

import pytest

from src.services.bank import bank_extract as extract
from src.services.bank.exceptions import BankAmountExtractionError


def test_extract_amount_parses_bank_confirmation_amount(monkeypatch) -> None:
    monkeypatch.setattr(
        extract,
        "extract_text",
        lambda _path: "Some text\nIznos EUR 2,180.00\nMore text",
    )

    assert extract.extract_amount(Path("bank-form.pdf")) == 2180.0


def test_extract_amount_raises_when_amount_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(extract, "extract_text", lambda _path: "No amount here")

    with pytest.raises(BankAmountExtractionError, match="Amount not found"):
        extract.extract_amount(Path("bank-form.pdf"))
