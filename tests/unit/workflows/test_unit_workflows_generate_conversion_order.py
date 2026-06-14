from datetime import datetime
from pathlib import Path

import pytest

from src.storage.orm.database import Database
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.workflows.tasks import generate_conversion_order as workflow
from tests.helpers.database import build_test_database_url, initialize_test_database


def test_generate_conversion_order_uses_conversion_amount_and_logs_amounts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name="Acme Ltd",
        company_address="Belgrade",
        city="Belgrade",
        service_agreement_date=datetime(2025, 6, 10),
    )
    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder="John Doe",
        account_holder_email="john@example.com",
        account_holder_address="Amsterdam",
        amount=1500,
        bank_name="ABN AMRO",
        account_number="123456789",
        iban="NL91ABNA0417164300",
        bic="ABNANL2A",
    )

    captured: dict[str, object] = {}

    def fake_generate_conversion_order(*, template_path: Path, output_pdf_path: Path, data: object) -> None:
        captured["template_path"] = template_path
        captured["output_pdf_path"] = output_pdf_path
        captured["data"] = data
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        output_pdf_path.write_bytes(b"%PDF-1.7\n")

    monkeypatch.setattr(workflow, "generate_conversion_order", fake_generate_conversion_order)
    monkeypatch.setattr(workflow, "apply_signature_to_pdf", lambda output_pdf_path, signature: None)

    caplog.set_level("INFO")

    output_path = workflow.generate_conversion_order_pdf(
        telegram_id=123,
        invoice_amount_eur=1500,
        bank_received_amount_eur=1450.75,
        conversion_amount_eur=1200.5,
        output_dir=tmp_path,
    )

    assert output_path.exists()
    assert captured["data"].exchange_amount_eur == "1200.50"
    assert "Preparing transfer request: invoice=1500 EUR, received=1450.75 EUR, exchange=1200.5 EUR" in caplog.text
    assert "Rendering transfer request document with exchange amount: 1200.5 EUR" in caplog.text
