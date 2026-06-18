from pathlib import Path

from cryptography.fernet import Fernet

from src.infrastructure.security.signature_cipher import SignatureCipher
from src.integrations.telegram.handlers.profile_handlers import ProfileHandlers
from src.integrations.telegram.state_service import UserStateService
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import Signature, UserConfig
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from tests.fakes.fake_telegram import FakeTelegramClient


def test_profile_screen_shows_status_summary_and_missing_fields(tmp_path: Path) -> None:
    SignatureCipher._cipher = None
    from src.utils.credentials import EnvVar

    EnvVar.reset_dotenv_cache()
    build_storage_dependencies()
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
        bank_confirmation_email_sender="bank@example.com",
        bank_confirmation_email_recipient="company@example.com",
        bank_confirmation_email_subject_contains="payment confirmation",
    )
    UserConfig.upsert(telegram_id=123, invoice_amount_eur=566)
    source = tmp_path / "signature.png"
    source.write_bytes(b"signature-bytes")
    encrypted = tmp_path / "signature.enc"
    SignatureCipher._cipher = None
    from src.utils.credentials import EnvVar

    EnvVar.reset_dotenv_cache()
    import os

    os.environ["SIGNATURE_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
    SignatureCipher.encrypt_file(source, encrypted)
    Signature.create(owner_telegram_id=123, signature_path=encrypted, signature_hash="hash")

    handlers.show_profile(123)

    message = telegram_client.sent_messages[0]
    assert "👤 Профиль" in message
    assert "🏢 Компания         ✔️" in message
    assert "🏦 Реквизиты        ✔️" in message
    assert "💳 Платёж           ➖" in message
    assert "✍️ Подпись          ✔️" in message
    assert "💰 Invoice          ✔️" in message
    assert "• payment_code" in message
    assert "• payment_description" in message
    assert "• Bank email sender: bank@example.com" in message
    assert "• Bank email recipient: company@example.com" in message
    assert "• Bank email subject contains: payment confirmation" in message


def test_profile_screen_marks_signature_unusable_when_file_is_missing(tmp_path: Path) -> None:
    build_storage_dependencies()
    telegram_client = FakeTelegramClient()
    handlers = ProfileHandlers(telegram_client, UserStateService)

    Signature.create(owner_telegram_id=123, signature_path=tmp_path / "missing-signature.enc", signature_hash="hash")

    handlers.show_profile(123)

    assert "✍️ Подпись          ⭕" in telegram_client.sent_messages[0]
    assert "• Не загружена" in telegram_client.sent_messages[0]
