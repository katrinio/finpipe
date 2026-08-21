"""Unit-тесты доставки сгенерированного инвойса в Telegram."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.workflows import run_invoice_delivery
from src.workflows.run_invoice_delivery import generate_and_send_invoice
from tests.fakes.fake_telegram import FakeTelegramClient


def test_generate_and_send_invoice_sends_document_and_removes_temporary_files(tmp_path: Path) -> None:
    pdf_path = tmp_path / "invoice-2026-06.pdf"
    docx_path = tmp_path / "invoice-2026-06.docx"
    pdf_path.write_bytes(b"pdf")
    docx_path.write_bytes(b"docx")
    telegram_client = FakeTelegramClient()

    with (
        patch.object(run_invoice_delivery, "generate_invoice_pdf", return_value=pdf_path),
        patch.object(run_invoice_delivery, "TelegramClient", return_value=telegram_client),
    ):
        generate_and_send_invoice(chat_id=123)

    assert telegram_client.sent_documents == [(123, str(pdf_path))]
    assert not pdf_path.exists()
    assert not docx_path.exists()


def test_generate_and_send_invoice_cleans_up_when_telegram_send_fails(tmp_path: Path) -> None:
    pdf_path = tmp_path / "invoice-2026-06.pdf"
    docx_path = tmp_path / "invoice-2026-06.docx"
    pdf_path.write_bytes(b"pdf")
    docx_path.write_bytes(b"docx")
    telegram_client = FakeTelegramClient()

    with (
        patch.object(run_invoice_delivery, "generate_invoice_pdf", return_value=pdf_path),
        patch.object(run_invoice_delivery, "TelegramClient", return_value=telegram_client),
        patch.object(telegram_client, "send_document", side_effect=RuntimeError("Telegram unavailable")),
        pytest.raises(RuntimeError, match="Telegram unavailable"),
    ):
        generate_and_send_invoice(chat_id=123)

    assert not pdf_path.exists()
    assert not docx_path.exists()
