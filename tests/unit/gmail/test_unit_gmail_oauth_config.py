import json

import pytest

from src.integrations.gmail.gmail_oauth import GmailOAuth


def test_gmail_oauth_prefers_env_client_config(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials_path = tmp_path / "credentials.json"
    credentials_path.write_text(
        json.dumps(
            {
                "web": {
                    "client_id": "file-client-id",
                    "client_secret": "file-secret",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["https://old.example.test/oauth/gmail/callback"],
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("GMAIL_CLIENT_ID", "env-client-id")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "env-secret")
    monkeypatch.setenv("GMAIL_CREDENTIALS_PATH", str(credentials_path))

    config, source, client_type, client_id = GmailOAuth._load_client_config("https://new.example.test/oauth/gmail/callback")

    assert source == "env"
    assert client_type == "web"
    assert client_id == "env-client-id"
    assert config["web"]["client_id"] == "env-client-id"
    assert config["web"]["client_secret"] == "env-secret"
    assert config["web"]["redirect_uris"] == ["https://new.example.test/oauth/gmail/callback"]


def test_gmail_oauth_falls_back_to_credentials_file(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    callback_url = "https://example.test/oauth/gmail/callback"
    credentials_path = tmp_path / "credentials.json"
    credentials_path.write_text(
        json.dumps(
            {
                "web": {
                    "client_id": "file-client-id",
                    "client_secret": "file-secret",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [callback_url],
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("GMAIL_CLIENT_ID", raising=False)
    monkeypatch.delenv("GMAIL_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("GMAIL_CREDENTIALS_PATH", str(credentials_path))

    config, source, client_type, client_id = GmailOAuth._load_client_config(callback_url)

    assert source == "credentials_file"
    assert client_type == "web"
    assert client_id == "file-client-id"
    assert config["web"]["client_id"] == "file-client-id"
