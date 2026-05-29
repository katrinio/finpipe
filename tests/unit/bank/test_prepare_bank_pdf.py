import os

import pytest

from src.workflows import prepare_bank_pdf


def test_resolve_bank_template_returns_explicit_pdf(tmp_path) -> None:
    bank_pdf = tmp_path / "bank-form"
    bank_pdf.write_bytes(b"%PDF-1.7\n")

    assert prepare_bank_pdf.resolve_bank_template(bank_pdf) == bank_pdf


def test_resolve_bank_template_picks_newest_pdf_from_attachments(
    tmp_path,
    monkeypatch,
) -> None:
    old_pdf = tmp_path / "old-bank-form"
    new_pdf = tmp_path / "new-bank-form"
    text_file = tmp_path / "notes.txt"

    old_pdf.write_bytes(b"%PDF-1.7\n")
    new_pdf.write_bytes(b"%PDF-1.7\n")
    text_file.write_text("not a pdf", encoding="utf-8")

    os.utime(old_pdf, (1, 1))
    os.utime(new_pdf, (2, 2))

    monkeypatch.setattr(prepare_bank_pdf.Bank, "ATTACHMENTS_DIR", tmp_path)

    assert prepare_bank_pdf.resolve_bank_template(None) == new_pdf


def test_resolve_bank_template_raises_when_explicit_file_is_not_pdf(tmp_path) -> None:
    text_file = tmp_path / "bank-form.txt"
    text_file.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(ValueError, match="not a PDF"):
        prepare_bank_pdf.resolve_bank_template(text_file)
