import os

from scripts import bot_container_runtime


def test_loopback_database_url_is_translated_for_compose_without_changing_credentials() -> None:
    database_url = "postgresql+psycopg://finpipe:p%40ss@localhost:5433/finpipe?sslmode=disable"

    result = bot_container_runtime.container_database_url(database_url)

    assert result == "postgresql+psycopg://finpipe:p%40ss@postgres:5432/finpipe?sslmode=disable"


def test_non_loopback_database_url_is_not_changed() -> None:
    database_url = "postgresql+psycopg://finpipe:secret@database.example:6432/finpipe"

    assert bot_container_runtime.container_database_url(database_url) == database_url


def test_runtime_passes_translated_url_only_in_child_environment(monkeypatch) -> None:
    database_url = "postgresql+psycopg://finpipe:secret@localhost:5433/finpipe"
    captured_environment: dict[str, str] = {}

    monkeypatch.setenv("DATABASE_URL", database_url)

    def fake_execvpe(_file: str, _args: list[str], environment: dict[str, str]) -> None:
        captured_environment.update(environment)

    monkeypatch.setattr(bot_container_runtime.os, "execvpe", fake_execvpe)

    assert bot_container_runtime.main(["python", "-m", "example"]) == 0
    assert captured_environment["DATABASE_URL"].endswith("@postgres:5432/finpipe")
    assert os.environ["DATABASE_URL"] == database_url
