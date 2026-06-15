import pytest

from src.integrations.gmail.oauth_token_bootstrap import load_credentials_config, normalize_client_config


def test_normalize_client_config_accepts_installed() -> None:
    config = {
        "installed": {
            "client_id": "installed-client-id",
            "client_secret": "installed-secret",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    normalized = normalize_client_config(config)

    assert normalized == config


def test_normalize_client_config_converts_web_to_installed() -> None:
    config = {
        "web": {
            "client_id": "web-client-id",
            "client_secret": "web-secret",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["https://example.test/oauth/gmail/callback"],
        }
    }

    normalized = normalize_client_config(config)

    assert "installed" in normalized
    assert normalized["installed"]["client_id"] == "web-client-id"
    assert normalized["installed"]["client_secret"] == "web-secret"
    assert normalized["installed"]["redirect_uris"] == ["http://localhost"]


def test_load_credentials_config_requires_existing_file(tmp_path) -> None:
    missing = tmp_path / "missing-credentials.json"

    with pytest.raises(FileNotFoundError, match="Gmail credentials file not found"):
        load_credentials_config(missing)
