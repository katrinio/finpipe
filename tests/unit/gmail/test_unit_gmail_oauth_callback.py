from datetime import UTC, datetime, timedelta

import pytest
from cryptography.fernet import Fernet

from src.infrastructure.security.token_cipher import TokenCipher
from src.integrations.gmail.exceptions import (
    GmailOAuthError,
    GmailOAuthStateNotActiveError,
    GmailOAuthTokenExchangeError,
)
from src.integrations.gmail.gmail_oauth import GmailOAuthResult
from src.integrations.gmail.oauth_callback import GmailOAuthCallbackService
from src.storage.orm.database import Database
from src.storage.orm.system.oauth_session import OAuthSession
from src.storage.orm.user.gmail_account import GmailAccount
from tests.helpers.database import build_test_database_url, initialize_test_database


def test_successful_callback_connects_gmail_and_marks_session_used(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    monkeypatch.setenv("SIGNATURE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("GMAIL_OAUTH_CALLBACK_URL", "https://example.test/oauth/gmail/callback")
    TokenCipher._cipher = None

    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    session = OAuthSession.create(telegram_id=123, telegram_username="alice", state="state-1", expires_at=expires_at)
    monkeypatch.setattr(
        "src.integrations.gmail.oauth_callback.GmailOAuth.exchange_code",
        lambda code, callback_url: GmailOAuthResult(
            email="user@example.com",
            refresh_token="refresh-token",
            scopes="scope-a scope-b",
            expires_at=None,
        ),
    )

    result = GmailOAuthCallbackService.handle_callback(code="code-1", state="state-1", error=None)

    gmail_account = GmailAccount.get_by_owner(123)
    used_session = OAuthSession.get_by_state(session.state)
    assert result.ok is True
    assert gmail_account is not None
    assert gmail_account.gmail_refresh_token is not None
    assert gmail_account.gmail_email == "user@example.com"
    assert used_session is not None
    assert used_session.status == "used"


@pytest.mark.parametrize(
    ("code", "state", "error", "message"),
    [
        (None, "state-1", None, "Missing code"),
        ("code-1", None, None, "Missing state"),
        ("code-1", "state-1", "access_denied", "OAuth error: access_denied"),
    ],
)
def test_callback_validation_errors_raise(code, state, error, message) -> None:
    with pytest.raises(GmailOAuthError, match=message):
        GmailOAuthCallbackService.handle_callback(code=code, state=state, error=error)


def test_invalid_state_raises_gmail_oauth_error(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    monkeypatch.setenv("GMAIL_OAUTH_CALLBACK_URL", "https://example.test/oauth/gmail/callback")

    with pytest.raises(GmailOAuthError, match="Invalid OAuth state"):
        GmailOAuthCallbackService.handle_callback(code="code-1", state="missing-state", error=None)


def test_callback_service_wraps_unexpected_failure(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    monkeypatch.setenv("GMAIL_OAUTH_CALLBACK_URL", "https://example.test/oauth/gmail/callback")
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    session = OAuthSession.create(telegram_id=123, telegram_username="alice", state="state-1", expires_at=expires_at)
    monkeypatch.setattr(
        "src.integrations.gmail.oauth_callback.GmailOAuth.exchange_code",
        lambda code, callback_url: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with pytest.raises(GmailOAuthError, match="Callback processing failed"):
        GmailOAuthCallbackService.handle_callback(code="code-1", state="state-1", error=None)

    failed_session = OAuthSession.get_by_state(session.state)
    assert failed_session is not None
    assert failed_session.status == "failed"


def test_reused_state_raises_specific_error(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    monkeypatch.setenv("GMAIL_OAUTH_CALLBACK_URL", "https://example.test/oauth/gmail/callback")
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    OAuthSession.create(telegram_id=123, telegram_username="alice", state="state-1", expires_at=expires_at)
    OAuthSession.mark_used("state-1")

    with pytest.raises(GmailOAuthStateNotActiveError, match="OAuth state is not active"):
        GmailOAuthCallbackService.handle_callback(code="code-1", state="state-1", error=None)


def test_token_exchange_failure_marks_session_failed(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    monkeypatch.setenv("GMAIL_OAUTH_CALLBACK_URL", "https://example.test/oauth/gmail/callback")
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    session = OAuthSession.create(telegram_id=123, telegram_username="alice", state="state-1", expires_at=expires_at)
    monkeypatch.setattr(
        "src.integrations.gmail.oauth_callback.GmailOAuth.exchange_code",
        lambda code, callback_url: (_ for _ in ()).throw(GmailOAuthTokenExchangeError("Failed to exchange OAuth code for Gmail credentials")),
    )

    with pytest.raises(GmailOAuthTokenExchangeError, match="Failed to exchange OAuth code for Gmail credentials"):
        GmailOAuthCallbackService.handle_callback(code="code-1", state="state-1", error=None)

    failed_session = OAuthSession.get_by_state(session.state)
    assert failed_session is not None
    assert failed_session.status == "failed"
