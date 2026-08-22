from pathlib import Path


def test_production_deploy_does_not_reference_removed_web_service() -> None:
    project_root = Path(__file__).resolve().parents[2]
    workflow = (project_root / ".github/workflows/deploy-finpipe.yml").read_text()

    assert "finpipe-web" not in workflow


def test_production_deploy_runs_single_migration_before_starting_bot() -> None:
    project_root = Path(__file__).resolve().parents[2]
    workflow = (project_root / ".github/workflows/deploy-finpipe.yml").read_text()

    migration_command = "docker compose -f docker-compose.yml run --rm finpipe-bot alembic upgrade head"
    start_command = "docker compose -f docker-compose.yml up -d --wait --wait-timeout 120 finpipe-bot --remove-orphans"

    assert workflow.count("alembic upgrade head") == 1
    assert workflow.index("docker compose -f docker-compose.yml stop finpipe-bot") < workflow.index(migration_command)
    assert workflow.index(migration_command) < workflow.index(start_command)


def test_production_deploy_backs_up_before_migration_and_waits_for_readiness() -> None:
    project_root = Path(__file__).resolve().parents[2]
    workflow = (project_root / ".github/workflows/deploy-finpipe.yml").read_text()

    backup_command = "python -m src.workflows.monitoring.backup_database"
    migration_command = "alembic upgrade head"

    assert "cancel-in-progress: false" in workflow
    assert workflow.index(backup_command) < workflow.index(migration_command)
    assert "--wait --wait-timeout 120 finpipe-bot" in workflow
    assert "schema_migrated=1" in workflow
    assert "automatic rollback is intentionally disabled" in workflow
    assert "logs --tail=100 postgres" in workflow
    assert "postgres --remove-orphans" in workflow


def test_production_compose_uses_secret_configuration_and_persistent_backups() -> None:
    project_root = Path(__file__).resolve().parents[2]
    compose = (project_root / "docker-compose.yml").read_text()

    assert "finpipe:finpipe" not in compose
    assert "DATABASE_URL: ${DATABASE_URL:" in compose
    assert "./backups:/app/backups" in compose
    assert 'test: ["CMD", "pg_isready", "--quiet"]' in compose
    assert 'finpipe-postgres-runtime", "--healthcheck' not in compose
    assert 'entrypoint: ["python", "/app/scripts/bot_container_runtime.py"]' in compose
    assert '"/app/scripts/bot_container_runtime.py", "python", "-m", "src.workflows.readiness"' in compose


def test_distributed_database_url_uses_the_compose_postgres_service() -> None:
    project_root = Path(__file__).resolve().parents[2]
    env_dist = (project_root / ".env.dist").read_text()

    database_url = next(line for line in env_dist.splitlines() if line.startswith("DATABASE_URL="))
    assert "@postgres:5432/" in database_url
    assert "localhost" not in database_url


def test_production_deploy_retries_only_ssh_transport_failures() -> None:
    project_root = Path(__file__).resolve().parents[2]
    workflow = (project_root / ".github/workflows/deploy-finpipe.yml").read_text()

    assert "appleboy/ssh-action" not in workflow
    assert "for attempt in 1 2 3" in workflow
    assert 'if [ "$exit_code" -ne 255 ]' in workflow
    assert "timeout 20m ssh" in workflow


def test_ci_postgres_health_command_is_a_single_docker_option_value() -> None:
    project_root = Path(__file__).resolve().parents[2]
    workflow = (project_root / ".github/workflows/quality_tests.yml").read_text()

    assert "--health-cmd pg_isready" in workflow
    assert "--health-cmd '" not in workflow
    assert '--health-cmd "' not in workflow
