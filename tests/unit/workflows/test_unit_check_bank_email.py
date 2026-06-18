from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from src.workflows.monitoring import check_bank_email
from tests.fakes.fake_telegram import FakeTelegramClient

_USER_A = SimpleNamespace(telegram_id=111)
_USER_B = SimpleNamespace(telegram_id=222)

_BANK_EMAIL = SimpleNamespace(
    message_id="msg-1",
    sender="bank@example.com",
    subject="Зачисление средств",
    date="Mon, 3 Jun 2026 09:00:00 +0200",
    thread_id="thread-1",
)


def test_skips_outside_check_period() -> None:
    assert not check_bank_email._is_check_period(date(2026, 6, 1))
    assert not check_bank_email._is_check_period(date(2026, 6, 7))


def test_active_during_check_period() -> None:
    for day in range(2, 7):
        assert check_bank_email._is_check_period(date(2026, 6, day))


def test_run_check_skips_outside_period(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_bank_email.AllowedUser, "list_all", lambda: [_USER_A])

    result = check_bank_email.run_check(today=date(2026, 6, 1))

    assert result == 0


def test_check_user_skips_when_gmail_not_connected(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.integrations.gmail.exceptions import GmailOAuthError

    fake = FakeTelegramClient()
    monkeypatch.setattr(check_bank_email, "get_gmail_service", lambda _tid: (_ for _ in ()).throw(GmailOAuthError("not connected")))

    result = check_bank_email.check_user(_USER_A.telegram_id, fake)

    assert result is False
    assert fake.sent_messages == []


def test_check_user_skips_when_no_email(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeTelegramClient()
    monkeypatch.setattr(check_bank_email, "get_gmail_service", lambda _tid: object())
    monkeypatch.setattr(check_bank_email, "find_bank_email", lambda _service, owner_telegram_id: None)

    result = check_bank_email.check_user(_USER_A.telegram_id, fake)

    assert result is False
    assert fake.sent_messages == []


def test_check_user_skips_when_already_notified(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeTelegramClient()
    monkeypatch.setattr(check_bank_email, "get_gmail_service", lambda _tid: object())
    monkeypatch.setattr(check_bank_email, "find_bank_email", lambda _service, owner_telegram_id: _BANK_EMAIL)
    monkeypatch.setattr(
        check_bank_email.ProcessedMessage,
        "is_processed",
        lambda key: key == check_bank_email._notification_key(_USER_A.telegram_id, _BANK_EMAIL.message_id),
    )

    result = check_bank_email.check_user(_USER_A.telegram_id, fake)

    assert result is False
    assert fake.sent_messages == []


def test_check_user_notifies_and_marks_when_new_email(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeTelegramClient()
    marked: list[str] = []
    monkeypatch.setattr(check_bank_email, "get_gmail_service", lambda _tid: object())
    monkeypatch.setattr(check_bank_email, "find_bank_email", lambda _service, owner_telegram_id: _BANK_EMAIL)
    monkeypatch.setattr(check_bank_email.ProcessedMessage, "is_processed", lambda _key: False)
    monkeypatch.setattr(check_bank_email.ProcessedMessage, "mark_as_processed", lambda key: marked.append(key))

    result = check_bank_email.check_user(_USER_A.telegram_id, fake)

    assert result is True
    assert len(fake.sent_messages_with_chat_ids) == 1
    chat_id, text = fake.sent_messages_with_chat_ids[0]
    assert chat_id == _USER_A.telegram_id
    assert "📬" in text
    assert _BANK_EMAIL.subject in text
    assert marked == [check_bank_email._notification_key(_USER_A.telegram_id, _BANK_EMAIL.message_id)]


def test_run_check_notifies_multiple_users(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeTelegramClient()
    monkeypatch.setattr(check_bank_email.AllowedUser, "list_all", lambda: [_USER_A, _USER_B])
    monkeypatch.setattr(check_bank_email, "TelegramClient", lambda: fake)
    monkeypatch.setattr(check_bank_email, "get_gmail_service", lambda _tid: object())
    monkeypatch.setattr(check_bank_email, "find_bank_email", lambda _service, owner_telegram_id: _BANK_EMAIL)
    monkeypatch.setattr(check_bank_email.ProcessedMessage, "is_processed", lambda _key: False)
    monkeypatch.setattr(check_bank_email.ProcessedMessage, "mark_as_processed", lambda _key: None)

    result = check_bank_email.run_check(today=date(2026, 6, 3))

    assert result == 2
    notified_ids = [chat_id for chat_id, _ in fake.sent_messages_with_chat_ids]
    assert set(notified_ids) == {_USER_A.telegram_id, _USER_B.telegram_id}


def test_run_check_user_error_does_not_abort_others(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeTelegramClient()
    monkeypatch.setattr(check_bank_email.AllowedUser, "list_all", lambda: [_USER_A, _USER_B])
    monkeypatch.setattr(check_bank_email, "TelegramClient", lambda: fake)

    def failing_for_first(tid: int) -> object:
        if tid == _USER_A.telegram_id:
            raise RuntimeError("boom")
        return object()

    monkeypatch.setattr(check_bank_email, "get_gmail_service", failing_for_first)
    monkeypatch.setattr(check_bank_email, "find_bank_email", lambda _service, owner_telegram_id: _BANK_EMAIL)
    monkeypatch.setattr(check_bank_email.ProcessedMessage, "is_processed", lambda _key: False)
    monkeypatch.setattr(check_bank_email.ProcessedMessage, "mark_as_processed", lambda _key: None)

    result = check_bank_email.run_check(today=date(2026, 6, 3))

    assert result == 1
    assert fake.sent_messages_with_chat_ids[0][0] == _USER_B.telegram_id


def test_notification_keys_are_per_user() -> None:
    key_a = check_bank_email._notification_key(_USER_A.telegram_id, "msg-1")
    key_b = check_bank_email._notification_key(_USER_B.telegram_id, "msg-1")
    assert key_a != key_b


def test_main_returns_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_bank_email.EnvVar, "load_dotenv", lambda: None)
    monkeypatch.setattr(check_bank_email, "run_check", lambda **_: 0)
    assert check_bank_email.main() == 0


def test_main_returns_one_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_bank_email.EnvVar, "load_dotenv", lambda: None)
    monkeypatch.setattr(check_bank_email, "run_check", lambda **_: (_ for _ in ()).throw(RuntimeError("boom")))
    assert check_bank_email.main() == 1
