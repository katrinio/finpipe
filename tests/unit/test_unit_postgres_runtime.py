import subprocess

from scripts import postgres_runtime


def test_database_url_is_the_only_source_for_postgres_child_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://finpipe:p%40ssword@postgres:5433/finpipe_db",
    )

    environment = postgres_runtime.connection_environment()

    assert environment["PGHOST"] == "postgres"
    assert environment["PGPORT"] == "5433"
    assert environment["PGDATABASE"] == "finpipe_db"
    assert environment["PGUSER"] == "finpipe"
    assert environment["PGPASSWORD"] == "p@ssword"


def test_postgres_healthcheck_does_not_put_credentials_in_process_arguments(monkeypatch) -> None:
    database_url = "postgresql+psycopg://finpipe:secret@postgres:5432/finpipe"
    monkeypatch.setenv("DATABASE_URL", database_url)
    captured_command: list[str] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        captured_command.extend(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(postgres_runtime.subprocess, "run", fake_run)

    assert postgres_runtime.run_healthcheck() == 0
    assert captured_command == ["pg_isready", "--quiet"]
    assert database_url not in " ".join(captured_command)
    assert "secret" not in " ".join(captured_command)


def test_postgres_runtime_error_does_not_print_database_url(monkeypatch, capsys) -> None:
    database_url = "postgresql+psycopg://finpipe:secret@postgres:not-a-port/finpipe"
    monkeypatch.setenv("DATABASE_URL", database_url)

    assert postgres_runtime.main(["--healthcheck"]) == 1

    captured = capsys.readouterr()
    assert database_url not in captured.err
    assert "secret" not in captured.err
