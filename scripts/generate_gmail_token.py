"""Generate a local Gmail token.json using browser-based OAuth."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from src.integrations.gmail.oauth_token_bootstrap import (
    describe_expiry,
    get_token_info,
    load_credentials_config,
    refresh_credentials,
    run_local_gmail_oauth_flow,
    save_credentials,
)
from src.utils.credentials import EnvVar


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger = logging.getLogger("generate_gmail_token")

    credentials_path = EnvVar.get_env_path("GMAIL_CREDENTIALS_PATH")
    token_path = EnvVar.get_env_path("GMAIL_TOKEN_PATH")

    logger.info("Using credentials file: %s", credentials_path)
    logger.info("Will save token to: %s", token_path)

    if not credentials_path.exists():
        raise FileNotFoundError(f"Gmail credentials file not found: {credentials_path}")

    load_credentials_config(credentials_path)
    credentials = run_local_gmail_oauth_flow(credentials_path)

    if credentials.expired and credentials.refresh_token:
        credentials = refresh_credentials(credentials)
    elif credentials.token is None:
        from google.auth.transport.requests import Request

        credentials.refresh(Request())

    save_credentials(credentials, token_path)

    if not token_path.exists():
        raise RuntimeError(f"Failed to save Gmail token file: {token_path}")

    info = get_token_info(credentials)
    logger.info("Saved token file: %s", token_path)
    logger.info("Authorized email: %s", info.email or "unknown")
    logger.info("Access token expiry: %s", describe_expiry(info.expiry))
    logger.info("Refresh token present: %s", "yes" if info.has_refresh_token else "no")
    logger.info("Gmail OAuth token generation completed at %s", datetime.now(UTC).isoformat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
