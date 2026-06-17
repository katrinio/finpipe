from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _mock_storage_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevents unit tests from touching the database during app lifespan."""
    monkeypatch.setattr(
        "src.interfaces.web.app.build_storage_dependencies",
        MagicMock(),
    )
