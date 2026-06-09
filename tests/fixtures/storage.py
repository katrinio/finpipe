import pytest

from tests.fakes.storage import FakeStorage, FakeTelegramUpdateStorage


@pytest.fixture
def fake_storage():
    def factory(allowed_ids: set[int] | None = None) -> FakeStorage:
        return FakeStorage(allowed_ids or set())

    return factory


@pytest.fixture
def fake_update_storage() -> FakeTelegramUpdateStorage:
    return FakeTelegramUpdateStorage()
