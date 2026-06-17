from src.workflows import run_bank_request
from tests.fakes.fake_telegram import FakeTelegramClient


class FakeOwner:
    telegram_id = 123


def test_run_bank_request_returns_error_when_bank_email_settings_missing(monkeypatch) -> None:
    telegram_client = FakeTelegramClient()
    monkeypatch.setattr(run_bank_request, "configure_logging", lambda: None)
    monkeypatch.setattr(run_bank_request.EnvVar, "get_dotenv", lambda: None)
    monkeypatch.setattr(run_bank_request, "build_storage_dependencies", lambda: None)
    monkeypatch.setattr(run_bank_request, "TelegramClient", lambda: telegram_client)
    monkeypatch.setattr(run_bank_request.AllowedUser, "get_owner", lambda: FakeOwner())
    monkeypatch.setattr(
        run_bank_request,
        "fetch_bank_email_workflow",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("missing settings")),
    )

    assert run_bank_request.main() == 1
    assert telegram_client.sent_messages == [
        "⚠️ Bank email search settings are missing.\n"
        "Fill bank_confirmation_email.sender, bank_confirmation_email.recipient and bank_confirmation_email.subject_contains in the profile."
    ]
