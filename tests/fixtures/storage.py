import pytest

from tests.fakes.fake_storage import FakeTelegramUpdateStorage


@pytest.fixture
def fake_update_storage() -> FakeTelegramUpdateStorage:
    return FakeTelegramUpdateStorage()
