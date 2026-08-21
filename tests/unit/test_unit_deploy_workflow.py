from pathlib import Path


def test_production_deploy_does_not_reference_removed_web_service() -> None:
    project_root = Path(__file__).resolve().parents[2]
    workflow = (project_root / ".github/workflows/deploy-finpipe.yml").read_text()

    assert "finpipe-web" not in workflow
