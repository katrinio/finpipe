from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials

from src.infrastructure.security.token_cipher import TokenCipher
from src.integrations.gmail import auth
from src.storage.orm.database import Database, build_sqlite_url
from src.storage.orm.user.gmail_account import GmailAccount
from tests.helpers.database import initialize_test_database


def test_load_connected_account_credentials_refreshes_gmail_account_token(tmp_path, monkeypatch) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    initialize_test_database(database)
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "123")
    monkeypatch.setenv("SIGNATURE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("GMAIL_CLIENT_ID", "client-id")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "client-secret")
    TokenCipher._cipher = None
    GmailAccount.update_gmail_credentials(
        telegram_id=123,
        gmail_email="user@example.com",
        gmail_refresh_token=TokenCipher.encrypt("refresh-token"),
    )
    refresh_calls: list[str | None] = []

    def fake_refresh(self, request) -> None:
        refresh_calls.append(self.refresh_token)
        self.token = "access-token"

    monkeypatch.setattr(Credentials, "refresh", fake_refresh)

    credentials = auth.load_connected_account_credentials()

    assert credentials is not None
    assert credentials.refresh_token == "refresh-token"
    assert credentials.client_id == "client-id"
    assert credentials.client_secret == "client-secret"
    assert refresh_calls == ["refresh-token"]


def test_get_gmail_service_prefers_connected_account_credentials(tmp_path, monkeypatch) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    initialize_test_database(database)
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "123")
    monkeypatch.setenv("SIGNATURE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("GMAIL_CLIENT_ID", "client-id")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("GMAIL_TOKEN_PATH", str(tmp_path / "missing-token.json"))
    TokenCipher._cipher = None
    GmailAccount.update_gmail_credentials(
        telegram_id=123,
        gmail_email="user@example.com",
        gmail_refresh_token=TokenCipher.encrypt("refresh-token"),
    )
    built_credentials: list[Credentials] = []

    def fake_refresh(self, request) -> None:
        self.token = "access-token"

    def fake_build(service_name, version, credentials, cache_discovery):
        built_credentials.append(credentials)
        return {"service": service_name, "version": version, "cache_discovery": cache_discovery}

    monkeypatch.setattr(Credentials, "refresh", fake_refresh)
    monkeypatch.setattr(auth, "build", fake_build)

    service = auth.get_gmail_service()

    assert service == {"service": "gmail", "version": "v1", "cache_discovery": False}
    assert len(built_credentials) == 1
    assert built_credentials[0].refresh_token == "refresh-token"
