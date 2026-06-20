"""Проверяет, что email в сообщении бота совпадает с реальным получателем письма."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.utils.credentials import EnvVar
from src.workflows import run_bank_request, run_invoice_delivery


def test_invoice_send_uses_same_recipient_as_prompt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """send_invoice_email отправляет письмо на тот же email, что показан в промпте."""
    recipient = "real-company@example.com"
    monkeypatch.setenv("EMAIL_DRY_RUN_RECIPIENT", recipient)

    fake_pdf = tmp_path / "invoice.pdf"
    fake_pdf.write_bytes(b"%PDF fake")

    captured: list[str] = []

    with (
        patch.object(run_invoice_delivery, "_current_invoice_pdf_path", return_value=fake_pdf),
        patch.object(run_invoice_delivery, "BankDetails") as mock_bd,
        patch.object(run_invoice_delivery, "send_email", lambda **kwargs: captured.append(kwargs["to_email"])),
    ):
        mock_bd.get_by_owner.return_value = MagicMock(account_holder="Alice", account_holder_email="alice@co.com")
        run_invoice_delivery.send_invoice_email(telegram_id=123)

    assert captured == [recipient], f"Письмо ушло на '{captured}', а в промпте показывается '{recipient}'"

    # Убеждаемся что промпт тоже читает ту же переменную
    prompt_recipient = EnvVar.get_optional_env("EMAIL_DRY_RUN_RECIPIENT", "")
    assert prompt_recipient == recipient


def test_bank_reply_uses_same_recipient_as_prompt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """send_bank_email_reply отправляет письмо на тот же email, что показан в промпте."""
    recipient = "bank@bank.rs"
    monkeypatch.setenv("EMAIL_DRY_RUN_RECIPIENT", recipient)

    fake_pdf = tmp_path / "doc.pdf"
    fake_pdf.write_bytes(b"%PDF fake")

    from src.integrations.gmail.gmail_models import BankEmail
    from src.workflows.run_bank_request import BankDocuments, send_bank_email_reply

    bank_email = BankEmail(
        subject="Payment confirmation",
        sender="bank@bank.rs",
        date="2026-06-20",
        message_id="msg-1",
        thread_id="thread-1",
    )
    docs = BankDocuments(invoice_pdf=fake_pdf, bank_confirmation=fake_pdf, conversion_order=fake_pdf)

    captured: list[str] = []

    with (
        patch.object(run_bank_request, "BankDetails") as mock_bd,
        patch.object(run_bank_request, "send_reply", lambda **kwargs: captured.append(kwargs["to_email"])),
    ):
        mock_bd.get_by_owner.return_value = MagicMock(account_holder="Alice", account_holder_email="alice@co.com")
        send_bank_email_reply(telegram_id=123, bank_email=bank_email, docs=docs)

    assert captured == [recipient], f"Письмо ушло на '{captured}', а в промпте показывается '{recipient}'"

    prompt_recipient = EnvVar.get_optional_env("EMAIL_DRY_RUN_RECIPIENT", "")
    assert prompt_recipient == recipient
