from pathlib import Path

from src.utils.credentials import EnvVar


def test_env_path_points_to_project_root() -> None:
    project_root = Path(__file__).resolve().parents[3]

    assert project_root == EnvVar.PROJECT_ROOT
    assert project_root / ".env" == EnvVar.ENV_PATH
