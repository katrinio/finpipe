from __future__ import annotations

from pathlib import Path

import pytest

from src.constants import TestData
from src.storage.orm import UserConfig
from src.storage.orm.database import Database, build_sqlite_url
from src.utils.credentials import EnvVar
from src.workflows.tasks.generate_invoice import generate_invoice_pdf


def _patch_invoice_env(monkeypatch: pytest.MonkeyPatch) -> None:
    values = {
        "ACCOUNT_HOLDER": "John Doe",
        "ACCOUNT_HOLDER_ADDRESS": "Amsterdam",
        "ACCOUNT_BIC": "ABNANL2A",
        "ACCOUNT_IBAN": "NL91ABNA0417164300",
        "ACCOUNT_NUMBER": "123456789",
        "BANK_NAME": "ABN AMRO",
        "COMPANY_ADDRESS": "Belgrade",
        "COMPANY_NAME": "Acme Ltd",
    }

    def get_required_env(key: str) -> str:
        return values[key]

    monkeypatch.setattr(EnvVar, "get_required_env", staticmethod(get_required_env))
    monkeypatch.setattr(EnvVar, "get_optional_env", staticmethod(lambda key, default=None: default))


def test_generate_invoice_pdf_uses_user_config_invoice_amount(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    UserConfig.upsert(telegram_id=123, invoice_amount=1500)
    _patch_invoice_env(monkeypatch)

    output_path = generate_invoice_pdf(telegram_id=123, template_path=TestData.INVOICE_TEMPLATE_PATH, output_dir=tmp_path)

    assert output_path.exists()
    assert output_path.name.startswith("invoice-")


def test_generate_invoice_pdf_fails_when_invoice_amount_is_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    _patch_invoice_env(monkeypatch)

    with pytest.raises(ValueError, match="Сумма Invoice не указана"):
        generate_invoice_pdf(telegram_id=123, template_path=TestData.INVOICE_TEMPLATE_PATH, output_dir=tmp_path)
