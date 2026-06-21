"""Интеграционные тесты email workflow: реальные данные профиля из БД + FakeService."""

import base64
import email
import email.header
from datetime import datetime
from pathlib import Path

import pytest

from src.integrations.gmail.gmail_models import BankEmail
from src.integrations.gmail.gmail_sender import GmailSender
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import UserConfig
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.workflows.run_bank_request import BankDocuments, send_bank_email_reply
from src.workflows.run_invoice_delivery import send_invoice_email
from tests.fakes.fake_gmail import FakeService


def _decode_raw(body: dict) -> email.message.Message:
    return email.message_from_bytes(base64.urlsafe_b64decode(body["raw"]))


def _decode_header(msg: email.message.Message, name: str) -> str:
    return str(email.header.make_header(email.header.decode_header(msg[name])))


def _setup_profile(telegram_id: int = 123) -> None:
    build_storage_dependencies()
    UserConfig.upsert(telegram_id=telegram_id, invoice_amount_eur=2000)
    CompanyProfile.upsert(
        owner_telegram_id=telegram_id,
        company_name="Katrin Torsunova PR",
        company_address="Belgrade",
        service_agreement_date=datetime(2025, 5, 1),
    )
    BankDetails.upsert(
        owner_telegram_id=telegram_id,
        account_holder="KATRIN TORSUNOVA",
        account_holder_email="to.katrin.t@gmail.com",
        account_holder_address="Belgrade",
        amount=2000,
        bank_name="Raiffeisen",
        account_number="123456789",
        iban="RS35123456789",
        bic="RZBSRSBG",
    )


def test_send_invoice_email_subject_body_and_attachment_from_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.workflows import run_invoice_delivery

    _setup_profile(123)

    pdf = tmp_path / "invoice-2026-06.pdf"
    pdf.write_bytes(b"%PDF fake")

    service = FakeService(response={"id": "msg-invoice"})

    monkeypatch.setattr(run_invoice_delivery, "_current_invoice_pdf_path", lambda: pdf)
    monkeypatch.setattr(run_invoice_delivery.EnvVar, "get_required_env", lambda _name: "test@example.com")
    monkeypatch.setenv("EMAIL_DRY_RUN", "false")
    monkeypatch.setattr(
        run_invoice_delivery,
        "send_email",
        lambda telegram_id, to_email, subject, body, attachments: GmailSender(telegram_id=telegram_id, service=service).send_email(
            to_email=to_email, subject=subject, body=body, attachments=attachments
        ),
    )

    send_invoice_email(telegram_id=123)

    sent = service.users_client.messages_client.sent_bodies[0]
    parsed = _decode_raw(sent)

    subject = _decode_header(parsed, "Subject")
    assert "Invoice" in subject
    assert "Katrin Torsunova" in subject

    body_text = parsed.get_payload(0).get_payload(decode=True).decode()
    assert "С уважением" in body_text
    assert "Katrin Torsunova" in body_text
    assert "to.katrin.t@gmail.com" in body_text

    filenames = [part.get_filename() for part in parsed.walk() if part.get_filename()]
    assert "invoice-2026-06.pdf" in filenames
    assert not pdf.exists(), "PDF должен быть удалён после отправки"


def test_send_bank_email_reply_body_thread_and_three_attachments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.workflows import run_bank_request

    _setup_profile(123)

    invoice = tmp_path / "invoice.pdf"
    confirmation = tmp_path / "confirmation.pdf"
    conversion = tmp_path / "conversion.pdf"
    for f in (invoice, confirmation, conversion):
        f.write_bytes(b"%PDF fake")

    service = FakeService(response={"id": "msg-bank"})

    monkeypatch.setattr(run_bank_request.EnvVar, "get_required_env", lambda _name: "test@example.com")
    monkeypatch.setenv("EMAIL_DRY_RUN", "false")
    monkeypatch.setattr(
        run_bank_request,
        "send_reply",
        lambda telegram_id, thread_id, to_email, subject, body, attachments, cc="": GmailSender(telegram_id=telegram_id, service=service).send_reply(
            thread_id=thread_id,
            to_email=to_email,
            subject=subject,
            body=body,
            attachments=attachments,
            cc=cc,
        ),
    )

    bank_email = BankEmail(
        subject="Obaveštenje o uplati",
        sender="bank@raiffeisen.rs",
        date="2026-06-19",
        message_id="msg-bank-123",
        thread_id="thread-bank-456",
    )
    docs = BankDocuments(invoice_pdf=invoice, bank_confirmation=confirmation, conversion_order=conversion)

    send_bank_email_reply(telegram_id=123, bank_email=bank_email, docs=docs)

    sent = service.users_client.messages_client.sent_bodies[0]
    assert sent["threadId"] == "thread-bank-456"

    parsed = _decode_raw(sent)
    assert _decode_header(parsed, "Subject") == "Re: Obaveštenje o uplati"
    assert parsed["To"] == "bank@raiffeisen.rs"

    body_text = parsed.get_payload(0).get_payload(decode=True).decode()
    assert "Dobar dan" in body_text
    assert "Katrin Torsunova" in body_text
    assert "to.katrin.t@gmail.com" in body_text

    filenames = [part.get_filename() for part in parsed.walk() if part.get_filename()]
    assert len(filenames) == 3
