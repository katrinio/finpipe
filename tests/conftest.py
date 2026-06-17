import os

import pytest
from dotenv import load_dotenv

pytest_plugins = (
    "tests.fixtures.storage",
    "tests.fixtures.telegram",
)
load_dotenv()


@pytest.fixture(autouse=True)
def _use_test_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Points DATABASE_URL at the test database for every test that needs it."""
    if test_url := os.getenv("TEST_DATABASE_URL"):
        monkeypatch.setenv("DATABASE_URL", test_url)
