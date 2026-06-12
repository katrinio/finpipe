from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.integrations.telegram.states import UserState
from src.storage.orm import AllowedUser, DocumentGenerationHistory, DocumentGenerationStatus, DocumentType, KnownUser, Signature, UserConfig
from src.storage.orm.database import Database, build_sqlite_url
from src.storage.orm.system.oauth_session import OAuthSession
from src.storage.orm.system.user_state_storage import UserStateStorage


def test_orm_timestamps_are_stored_without_microseconds(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    AllowedUser.create(telegram_id=1, username="owner")
    allowed_user = AllowedUser.get_by_telegram_id(1)
    assert allowed_user is not None
    assert allowed_user.created_at.microsecond == 0

    KnownUser.upsert(telegram_id=2, username="known", first_name="Known")
    known_user = KnownUser.get_by_telegram_id(2)
    assert known_user is not None
    assert known_user.created_at.microsecond == 0
    assert known_user.last_seen_at.microsecond == 0

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
    assert oauth_session.created_at.microsecond == 0
    assert oauth_session.expires_at.microsecond == 0
    assert oauth_session.used_at is not None
    assert oauth_session.used_at.microsecond == 0

    DocumentGenerationHistory.add_attempt(DocumentType.INVOICE, "2026-05", telegram_id=4, status=DocumentGenerationStatus.SUCCESS)
    history_record = DocumentGenerationHistory.get_last_attempt(DocumentType.INVOICE, "2026-05")
    assert history_record is not None
    assert history_record.created_at.microsecond == 0


def test_updated_timestamps_are_stored_without_microseconds(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    UserConfig.upsert(telegram_id=10, invoice_amount=1000)
    UserConfig.upsert(telegram_id=10, invoice_amount=1500)
    user_config = UserConfig.get_by_owner(10)
    assert user_config is not None
    assert user_config.created_at.microsecond == 0
    assert user_config.updated_at.microsecond == 0

    UserStateStorage.upsert(owner_telegram_id=11, state=UserState.WAITING_INVOICE_AMOUNT)
    UserStateStorage.upsert(owner_telegram_id=11, state=UserState.WAITING_PROFILE_TEMPLATE_UPLOAD)
    user_state = UserStateStorage.get_by_owner(11)
    assert user_state is not None
    assert user_state.created_at.microsecond == 0
    assert user_state.updated_at is not None
    assert user_state.updated_at.microsecond == 0

    signature_path = tmp_path / "signature.enc"
    signature_path.write_text("signature")
    Signature.create(owner_telegram_id=12, signature_path=signature_path)
    Signature.create(owner_telegram_id=12, signature_path=signature_path)
    signature = Signature.get_by_owner(12)
    assert signature is not None
    assert signature.created_at.microsecond == 0
    assert signature.updated_at.microsecond == 0
