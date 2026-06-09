from pathlib import Path

import pytest

from src.utils.credentials import ENV_PATH_OVERRIDE, EnvVar


@pytest.fixture(autouse=True)
def reset_dotenv_cache():
    EnvVar.reset_dotenv_cache()
    yield
    EnvVar.reset_dotenv_cache()


def test_env_path_points_to_project_root() -> None:
    project_root = Path(__file__).resolve().parents[3]

    assert project_root == EnvVar.PROJECT_ROOT
    assert project_root / ".env" == EnvVar.ENV_PATH


def test_get_required_env_loads_dotenv_automatically(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("AUTO_LOADED_VALUE=from-dotenv\n", encoding="utf-8")
    monkeypatch.setenv(ENV_PATH_OVERRIDE, str(dotenv_path))
    monkeypatch.delenv("AUTO_LOADED_VALUE", raising=False)

    assert EnvVar.get_required_env("AUTO_LOADED_VALUE") == "from-dotenv"


def test_get_optional_env_loads_dotenv_automatically(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("OPTIONAL_VALUE=from-dotenv\n", encoding="utf-8")
    monkeypatch.setenv(ENV_PATH_OVERRIDE, str(dotenv_path))
    monkeypatch.delenv("OPTIONAL_VALUE", raising=False)

    assert EnvVar.get_optional_env("OPTIONAL_VALUE", "fallback") == "from-dotenv"


def test_process_env_takes_precedence_over_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("EXISTING_VALUE=from-dotenv\n", encoding="utf-8")
    monkeypatch.setenv(ENV_PATH_OVERRIDE, str(dotenv_path))
    monkeypatch.setenv("EXISTING_VALUE", "from-process")

    assert EnvVar.get_required_env("EXISTING_VALUE") == "from-process"


def test_get_env_path_resolves_relative_paths_from_project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("RELATIVE_PATH=token.json\n", encoding="utf-8")
    monkeypatch.setenv(ENV_PATH_OVERRIDE, str(dotenv_path))
    monkeypatch.delenv("RELATIVE_PATH", raising=False)

    assert EnvVar.get_env_path("RELATIVE_PATH") == EnvVar.PROJECT_ROOT / "token.json"


def test_get_required_env_reports_checked_dotenv_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dotenv_path = tmp_path / "missing.env"
    monkeypatch.setenv(ENV_PATH_OVERRIDE, str(dotenv_path))
    monkeypatch.delenv("MISSING_VALUE", raising=False)

    with pytest.raises(RuntimeError, match="MISSING_VALUE") as error:
        EnvVar.get_required_env("MISSING_VALUE")

    assert str(dotenv_path) in str(error.value)
