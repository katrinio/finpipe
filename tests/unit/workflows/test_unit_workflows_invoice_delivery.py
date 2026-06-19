"""Unit-тесты для run_invoice_delivery: email subject/body, отправка письма, удаление файла."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.workflows import run_invoice_delivery
from src.workflows.run_invoice_delivery import (
    _invoice_email_body,
    _invoice_email_subject,
    discard_invoice_pdf,
    generate_and_send_invoice,
    send_invoice_email,
)
from tests.fakes.fake_telegram import FakeTelegramClient

# ---------------------------------------------------------------------------
# subject / body helpers
# ---------------------------------------------------------------------------


def test_invoice_email_subject_uses_ru_month_and_title_case_name() -> None:
    result = _invoice_email_subject("KATRIN TORSUNOVA", month=date(2026, 6, 1))
    assert result == "Июнь Invoice - Katrin Torsunova"


def test_invoice_email_subject_may_month() -> None:
    result = _invoice_email_subject("JOHN DOE", month=date(2026, 5, 15))
    assert result == "Май Invoice - John Doe"


def test_invoice_email_body_contains_month_and_name() -> None:
    result = _invoice_email_body("KATRIN TORSUNOVA", month=date(2026, 6, 1))
    assert "июнь" in result
    assert "Katrin Torsunova" in result
    assert "Regards" in result


def test_invoice_email_body_may() -> None:
    result = _invoice_email_body("JOHN DOE", month=date(2026, 5, 15))
    assert "май" in result


# ---------------------------------------------------------------------------
# generate_and_send_invoice — PDF остаётся, docx удаляется
# ---------------------------------------------------------------------------


def test_generate_and_send_invoice_keeps_pdf_and_removes_docx(tmp_path: Path) -> None:
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

    assert pdf_path.exists(), "PDF должен остаться до подтверждения отправки"
    assert not docx_path.exists(), "docx должен быть удалён сразу"
    assert telegram_client.sent_documents == [(123, str(pdf_path))]


# ---------------------------------------------------------------------------
# send_invoice_email — письмо отправляется, PDF удаляется
# ---------------------------------------------------------------------------


def _fake_bank_details(account_holder: str = "KATRIN TORSUNOVA"):
    details = MagicMock()
    details.account_holder = account_holder
    return details


def test_send_invoice_email_calls_send_email_and_removes_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "invoice-2026-06.pdf"
    pdf_path.write_bytes(b"pdf")

    captured: dict = {}

    def fake_send_email(telegram_id, to_email, subject, body, attachments):
        captured["telegram_id"] = telegram_id
        captured["subject"] = subject
        captured["body"] = body
        captured["attachments"] = attachments

    with (
        patch.object(run_invoice_delivery, "_current_invoice_pdf_path", return_value=pdf_path),
        patch.object(run_invoice_delivery.BankDetails, "get_by_owner", return_value=_fake_bank_details()),
        patch.object(run_invoice_delivery.EnvVar, "get_required_env", return_value="test@example.com"),
        patch.object(run_invoice_delivery, "send_email", fake_send_email),
    ):
        send_invoice_email(telegram_id=123)

    assert captured["telegram_id"] == 123
    assert "Invoice" in captured["subject"]
    assert "Regards" in captured["body"]
    assert pdf_path in captured["attachments"]
    assert not pdf_path.exists(), "PDF должен быть удалён после отправки"


def test_send_invoice_email_removes_pdf_even_if_send_fails(tmp_path: Path) -> None:
    pdf_path = tmp_path / "invoice-2026-06.pdf"
    pdf_path.write_bytes(b"pdf")

    with (
        patch.object(run_invoice_delivery, "_current_invoice_pdf_path", return_value=pdf_path),
        patch.object(run_invoice_delivery.BankDetails, "get_by_owner", return_value=_fake_bank_details()),
        patch.object(run_invoice_delivery.EnvVar, "get_required_env", return_value="test@example.com"),
        patch.object(run_invoice_delivery, "send_email", side_effect=RuntimeError("smtp error")),
        pytest.raises(RuntimeError),
    ):
        send_invoice_email(telegram_id=123)

    assert not pdf_path.exists(), "PDF должен быть удалён даже при ошибке отправки"


# ---------------------------------------------------------------------------
# discard_invoice_pdf — файл удаляется без отправки
# ---------------------------------------------------------------------------


def test_discard_invoice_pdf_removes_file(tmp_path: Path) -> None:
    pdf_path = tmp_path / "invoice-2026-06.pdf"
    pdf_path.write_bytes(b"pdf")

    with patch.object(run_invoice_delivery, "_current_invoice_pdf_path", return_value=pdf_path):
        discard_invoice_pdf()

    assert not pdf_path.exists()


def test_discard_invoice_pdf_does_not_raise_if_file_missing(tmp_path: Path) -> None:
    pdf_path = tmp_path / "invoice-2026-06.pdf"

    with patch.object(run_invoice_delivery, "_current_invoice_pdf_path", return_value=pdf_path):
        discard_invoice_pdf()  # не должно кидать исключение
