from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.integrations.telegram.states import UserState
from src.storage.orm import AllowedUser, DocumentGenerationHistory, KnownUser, Signature, UserConfig
from src.storage.orm.database import Database
from src.storage.orm.system.document_generation_history import DocumentGenerationStatus, DocumentType
from src.storage.orm.system.oauth_session import OAuthSession
from src.storage.orm.system.user_state_storage import UserStateStorage
from tests.helpers.database import build_test_database_url, initialize_test_database


def test_orm_timestamps_are_stored_without_microseconds(tmp_path: Path) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)

    now = datetime.now(UTC)
    AllowedUser.create(telegram_id=1, username="owner")
    allowed_user = AllowedUser.get_by_telegram_id(1)
    assert allowed_user is not None
    assert abs((now - allowed_user.created_at).total_seconds()) < 5

    KnownUser.upsert(telegram_id=2, username="known", first_name="Known")
    known_user = KnownUser.get_by_telegram_id(2)
    assert known_user is not None
    assert abs((now - known_user.created_at).total_seconds()) < 5
    assert abs((now - known_user.last_seen_at).total_seconds()) < 5

    expires_at = datetime.now(UTC).replace(microsecond=987654) + timedelta(minutes=15)
    OAuthSession.create(
        telegram_id=3,
        telegram_username="oauth",
        state="state-1",
        expires_at=expires_at,
    )
    OAuthSession.mark_used("state-1")
    oauth_session = OAuthSession.get_by_state("state-1")
    assert oauth_session is not None
    assert abs((now - oauth_session.created_at).total_seconds()) < 5
    assert oauth_session.expires_at.microsecond == 987654
    assert oauth_session.used_at is not None
    assert abs((now - oauth_session.used_at).total_seconds()) < 5

    DocumentGenerationHistory.add_attempt(DocumentType.SALARY_INVOICE, "2026-05", telegram_id=4, status=DocumentGenerationStatus.SUCCESS)
    history_record = DocumentGenerationHistory.get_last_attempt(DocumentType.SALARY_INVOICE, "2026-05")
    assert history_record is not None
    assert abs((now - history_record.created_at).total_seconds()) < 5


def test_updated_timestamps_are_stored_without_microseconds(tmp_path: Path) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)

    now = datetime.now(UTC)
    UserConfig.upsert(telegram_id=10, invoice_amount_eur=1000)
    UserConfig.upsert(telegram_id=10, invoice_amount_eur=1500)
    user_config = UserConfig.get_by_owner(10)
    assert user_config is not None
    assert abs((now - user_config.created_at).total_seconds()) < 5
    assert abs((now - user_config.updated_at).total_seconds()) < 5

    UserStateStorage.upsert(owner_telegram_id=11, state=UserState.WAITING_INVOICE_AMOUNT)
    UserStateStorage.upsert(owner_telegram_id=11, state=UserState.WAITING_PROFILE_TEMPLATE_UPLOAD)
    user_state = UserStateStorage.get_by_owner(11)
    assert user_state is not None
    assert abs((now - user_state.created_at).total_seconds()) < 5
    assert user_state.updated_at is not None
    assert abs((now - user_state.updated_at).total_seconds()) < 5

    signature_path = tmp_path / "signature.enc"
    signature_path.write_text("signature")
    Signature.create(owner_telegram_id=12, signature_path=signature_path)
    Signature.create(owner_telegram_id=12, signature_path=signature_path)
    signature = Signature.get_by_owner(12)
    assert signature is not None
    assert abs((now - signature.created_at).total_seconds()) < 5
    assert abs((now - signature.updated_at).total_seconds()) < 5
