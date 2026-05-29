import logging
import os
from collections.abc import Sequence
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials

LOGGER = logging.getLogger(__name__)


class EnvVar:
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    ENV_PATH = PROJECT_ROOT / ".env"

    @classmethod
    def get_dotenv(cls) -> None:
        load_dotenv(cls.ENV_PATH)

    @classmethod
    def get_required_env(cls, name: str) -> str:
        value = os.getenv(name)
        if not value:
            msg = f"Missing required environment variable: {name}"
            raise RuntimeError(msg)

        return value

    @classmethod
    def get_env_path(cls, name: str) -> Path:
        value = EnvVar.get_required_env(name)
        if not value:
            message = f"Missing required environment variable: {name}"
            raise RuntimeError(message)

        path = Path(value).expanduser()
        if not path.is_absolute():
            path = EnvVar.PROJECT_ROOT / path
        return path

    @classmethod
    def load_credentials(cls, token_path: Path, scopes: Sequence[str] | None = None) -> Credentials | None:
        if not token_path.exists():
            LOGGER.info("Gmail OAuth token not found at %s", token_path)
            return None

        try:
            return Credentials.from_authorized_user_file(str(token_path), scopes)
        except ValueError as error:
            LOGGER.warning(
                "Ignoring invalid Gmail OAuth token at %s: %s",
                token_path,
                error,
            )
            return None
