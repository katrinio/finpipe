from pathlib import Path


def test_production_deploy_does_not_reference_removed_web_service() -> None:
    project_root = Path(__file__).resolve().parents[2]
    workflow = (project_root / ".github/workflows/deploy-finpipe.yml").read_text()

    assert "finpipe-web" not in workflow


def test_production_deploy_runs_single_migration_before_starting_bot() -> None:
    project_root = Path(__file__).resolve().parents[2]
    workflow = (project_root / ".github/workflows/deploy-finpipe.yml").read_text()

    migration_command = "docker compose -f docker-compose.yml run --rm finpipe-bot alembic upgrade head"
    start_command = "docker compose -f docker-compose.yml up -d finpipe-bot --remove-orphans"

    assert workflow.count("alembic upgrade head") == 1
    assert workflow.index("docker compose -f docker-compose.yml stop finpipe-bot") < workflow.index(migration_command)
    assert workflow.index(migration_command) < workflow.index(start_command)
