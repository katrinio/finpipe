import logging
import os
from pathlib import Path
from typing import Any

# from dotenv import load_dotenv
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"
GMAIL_SCOPES = ("https://www.googleapis.com/auth/gmail.readonly",)
load_dotenv(ENV_PATH)


def get_gmail_service() -> Any:
    token_path = get_env_path("GMAIL_TOKEN_PATH")
    credentials = load_credentials(token_path)

    if credentials and credentials.valid:
        LOGGER.info("Loaded valid Gmail OAuth token from %s", token_path)
    else:
        credentials = refresh_or_create_credentials(
            credentials,
            get_env_path("GMAIL_CREDENTIALS_PATH"),
        )
        save_credentials(credentials, token_path)

    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def get_env_path(name: str) -> Path:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path


def load_credentials(token_path: Path) -> Credentials | None:
    if not token_path.exists():
        LOGGER.info("Gmail OAuth token not found at %s", token_path)
        return None

    try:
        return Credentials.from_authorized_user_file(str(token_path), GMAIL_SCOPES)
    except ValueError as error:
        LOGGER.warning("Ignoring invalid Gmail OAuth token at %s: %s", token_path, error)
        return None


def refresh_or_create_credentials(
        credentials: Credentials | None,
        credentials_path: Path,
) -> Credentials:
    if credentials and credentials.expired and credentials.refresh_token:
        LOGGER.info("Refreshing expired Gmail OAuth token")
        credentials.refresh(Request())
        return credentials

    if not credentials_path.exists():
        raise FileNotFoundError(f"Gmail credentials file not found: {credentials_path}")

    LOGGER.info("Starting Gmail OAuth browser login")
    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), GMAIL_SCOPES)
    return flow.run_local_server(port=0)


def save_credentials(credentials: Credentials, token_path: Path) -> None:
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    LOGGER.info("Saved Gmail OAuth token to %s", token_path)
