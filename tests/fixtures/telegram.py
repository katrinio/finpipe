import pytest

from tests.fakes.fake_telegram import FakeTelegramClient


@pytest.fixture
def fake_telegram_client():
    def factory(updates=None):
        return FakeTelegramClient(updates)

    return factory
