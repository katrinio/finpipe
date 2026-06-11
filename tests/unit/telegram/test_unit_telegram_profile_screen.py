from __future__ import annotations

from pathlib import Path

from src.integrations.telegram.handlers.profile_handlers import ProfileHandlers
from src.integrations.telegram.state_service import UserStateService
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import Signature, UserConfig
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from tests.fakes.fake_telegram import FakeTelegramClient


def test_profile_screen_shows_status_summary_and_missing_fields(tmp_path: Path) -> None:
    build_storage_dependencies(tmp_path / "storage.sqlite3")
    telegram_client = FakeTelegramClient()
    handlers = ProfileHandlers(telegram_client, UserStateService)

    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name="Acme Software LLC",
        company_address="123 Innovation Street, Belgrade, Serbia",
        registration_number="12345678",
        city="Belgrade",
        payment_number="97",
    )
    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder="Acme Software LLC",
        bank_name="Example Bank Serbia",
        account_number="123456789",
        iban="RS35123456789012345678",
        bic="EXAMPLERSBG",
    )
    UserConfig.upsert(telegram_id=123, invoice_amount=566)
    Signature.create(owner_telegram_id=123, signature_path=tmp_path / "signature.png", signature_hash="hash")

    handlers.show_profile(123)

    assert telegram_client.sent_messages == [
        "👤 Профиль\n"
        "\n"
        "🏢 Компания         ✅\n"
        "🏦 Реквизиты        ✅\n"
        "💳 Платёж           ⚠️\n"
        "✍️ Подпись          ✅\n"
        "💰 Invoice          ✅\n"
        "\n"
        "Не хватает:\n"
        "• payment_code\n"
        "• payment_description\n"
        "\n"
        "🏢 Компания\n"
        "• Acme Software LLC\n"
        "• 123 Innovation Street, Belgrade, Serbia\n"
        "• Регистрационный номер: 12345678\n"
        "• Город: Belgrade\n"
        "\n"
        "🏦 Банковские реквизиты\n"
        "• Банк: Example Bank Serbia\n"
        "• Получатель: Acme Software LLC\n"
        "• Счёт: 123456789\n"
        "• IBAN: RS35123456789012345678\n"
        "• BIC: EXAMPLERSBG\n"
        "\n"
        "💳 Платёж\n"
        "• Номер платежа: 97\n"
        "• Код платежа: 🛑 не задано\n"
        "• Описание платежа: 🛑 не задано\n"
        "\n"
        "✍️ Подпись\n"
        "• ✅\n"
        "\n"
        "💰 Invoice\n"
        "• 566 EUR",
    ]
