import logging
import os
from collections.abc import Sequence
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials

LOGGER = logging.getLogger(__name__)
ENV_PATH_OVERRIDE = "FINPIPE_ENV_PATH"


def find_project_root(start: Path | None = None) -> Path:
    start_path = (start or Path(__file__)).resolve()
    current_path = start_path if start_path.is_dir() else start_path.parent

    for path in (current_path, *current_path.parents):
        if (path / "pyproject.toml").exists() and (path / "src").exists():
            return path

    return Path(__file__).resolve().parents[2]


def unique_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    result: list[Path] = []
    seen: set[Path] = set()

    for path in paths:
        resolved_path = path.expanduser().resolve()
        if resolved_path not in seen:
            result.append(resolved_path)
            seen.add(resolved_path)

    return tuple(result)


class EnvVar:
    PROJECT_ROOT = find_project_root()
    ENV_PATH = PROJECT_ROOT / ".env"
    _DOTENV_LOADED = False
    _LOADED_DOTENV_PATHS: tuple[Path, ...] = ()

    @classmethod
    def get_dotenv(cls) -> None:
        cls.load_dotenv(force=True)

    @classmethod
    def load_dotenv(cls, force: bool = False) -> None:
        if cls._DOTENV_LOADED and not force:
            return

        loaded_paths: list[Path] = []

        for path in cls.get_dotenv_paths():
            if not path.exists():
                LOGGER.debug("Skipping missing .env file: %s", path)
                continue

            load_dotenv(path, override=False)
            loaded_paths.append(path)
            LOGGER.debug("Loaded environment variables from %s", path)

        cls._LOADED_DOTENV_PATHS = tuple(loaded_paths)
        cls._DOTENV_LOADED = True

    @classmethod
    def get_dotenv_paths(cls) -> tuple[Path, ...]:
        paths: list[Path] = []
        override_path = os.getenv(ENV_PATH_OVERRIDE)

        if override_path:
            return unique_paths([Path(override_path)])

        paths.append(cls.ENV_PATH)

        cwd = Path.cwd().resolve()
        project_root = cls.PROJECT_ROOT.resolve()

        for path in (cwd, *cwd.parents):
            paths.append(path / ".env")
            if path == project_root:
                break

        return unique_paths(paths)

    @classmethod
    def reset_dotenv_cache(cls) -> None:
        cls._DOTENV_LOADED = False
        cls._LOADED_DOTENV_PATHS = ()

    @classmethod
    def get_required_env(cls, name: str) -> str:
        cls.load_dotenv()

        value = os.getenv(name)
        if not value:
            msg = f"Missing required environment variable: {name}. Checked .env files: {cls.format_dotenv_paths()}"
            raise RuntimeError(msg)

        return value

    @classmethod
    def get_optional_env(cls, name: str, default: str) -> str:
        cls.load_dotenv()
        return os.getenv(name) or default

    @classmethod
    def get_env_path(cls, name: str) -> Path:
        value = EnvVar.get_required_env(name)
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = EnvVar.PROJECT_ROOT / path
        return path

    @classmethod
    def format_dotenv_paths(cls) -> str:
        return ", ".join(str(path) for path in cls.get_dotenv_paths())

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
