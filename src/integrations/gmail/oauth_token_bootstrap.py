"""Helpers for generating and restoring Gmail OAuth tokens locally."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)
GMAIL_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
)


@dataclass(frozen=True, slots=True)
class GmailTokenInfo:
    email: str | None
    expiry: datetime | None
    has_refresh_token: bool


def load_credentials_config(credentials_path: Path) -> dict[str, Any]:
    if not credentials_path.exists():
        raise FileNotFoundError(f"Gmail credentials file not found: {credentials_path}")
    return json.loads(credentials_path.read_text(encoding="utf-8"))


def normalize_client_config(credentials_config: dict[str, Any]) -> dict[str, Any]:
    if "installed" in credentials_config:
        return {"installed": credentials_config["installed"]}
    if "web" in credentials_config:
        web_config = dict(credentials_config["web"])
        web_config["redirect_uris"] = ["http://localhost"]
        web_config["auth_uri"] = web_config.get("auth_uri", "https://accounts.google.com/o/oauth2/auth")
        web_config["token_uri"] = web_config.get("token_uri", "https://oauth2.googleapis.com/token")
        return {"installed": web_config}
    raise ValueError("Gmail credentials file must contain installed or web client config")


def build_installed_app_flow(credentials_path: Path) -> Any:
    from google_auth_oauthlib.flow import InstalledAppFlow

    credentials_config = load_credentials_config(credentials_path)
    normalized = normalize_client_config(credentials_config)
    return InstalledAppFlow.from_client_config(normalized, list(GMAIL_SCOPES))


def run_local_gmail_oauth_flow(credentials_path: Path) -> Any:
    LOGGER.info("Starting local Gmail OAuth flow using %s", credentials_path)
    flow = build_installed_app_flow(credentials_path)
    return flow.run_local_server(port=0, open_browser=True, prompt="consent")


def save_credentials(credentials: Any, token_path: Path) -> None:
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")


def refresh_credentials(credentials: Any) -> Any:
    from google.auth.transport.requests import Request

    credentials.refresh(Request())
    return credentials


def load_token(token_path: Path) -> Any | None:
    from google.oauth2.credentials import Credentials

    if not token_path.exists():
        return None
    try:
        return Credentials.from_authorized_user_file(str(token_path), list(GMAIL_SCOPES))
    except ValueError as error:
        LOGGER.warning("Ignoring invalid Gmail OAuth token at %s: %s", token_path, error)
        return None


def get_token_info(credentials: Any) -> GmailTokenInfo:
    email = getattr(credentials, "email", None)
    if not email:
        email = _load_email_from_userinfo(credentials)
    return GmailTokenInfo(
        email=email,
        expiry=getattr(credentials, "expiry", None),
        has_refresh_token=bool(getattr(credentials, "refresh_token", None)),
    )


def _load_email_from_userinfo(credentials: Any) -> str | None:
    try:
        from googleapiclient.discovery import build
    except ImportError:
        return None

    try:
        service = build("oauth2", "v2", credentials=credentials, cache_discovery=False)
        response = service.userinfo().get().execute()
    except Exception:
        return None

    return response.get("email")


def describe_expiry(expiry: datetime | None) -> str:
    if expiry is None:
        return "unknown"
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=UTC)
    remaining = expiry - datetime.now(UTC)
    if remaining <= timedelta(0):
        return f"expired at {expiry.isoformat()}"
    return f"expires at {expiry.isoformat()} ({remaining})"
