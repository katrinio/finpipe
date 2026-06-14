from datetime import UTC, datetime, timedelta

import pytest

from src.integrations.telegram.handlers.gmail_handlers import GmailHandlers
from src.integrations.telegram.ui.buttons import GmailButtons
from src.integrations.telegram.ui.messages import GmailMessagesV2
from src.storage.orm.database import Database
from src.storage.orm.system.oauth_session import OAuthSession
from tests.fakes.fake_telegram import FakeTelegramClient
from tests.helpers.database import build_test_database_url, initialize_test_database


def test_gmail_connect_sends_inline_authorization_button(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    telegram = FakeTelegramClient()
    handler = GmailHandlers(telegram)
    authorization_url = "https://accounts.google.com/o/oauth2/auth?state=state-1"
    callback_url = "https://example.test/oauth/gmail/callback"
    session = OAuthSession.create(
        telegram_id=123,
        telegram_username="alice",
        state="state-1",
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )
    build_calls: list[tuple[int, str | None, str]] = []

    monkeypatch.setattr("src.integrations.telegram.handlers.gmail_handlers.GmailOAuthSettings.is_callback_enabled", lambda: True)
    monkeypatch.setattr("src.integrations.telegram.handlers.gmail_handlers.GmailOAuthSettings.get_callback_url", lambda: callback_url)

    def fake_build_authorization_url(telegram_id: int, username: str | None, callback: str) -> tuple[str, OAuthSession]:
        build_calls.append((telegram_id, username, callback))
        return authorization_url, session

    monkeypatch.setattr(
        "src.integrations.telegram.handlers.gmail_handlers.GmailOAuth.build_authorization_url",
        fake_build_authorization_url,
    )

    handler.gmail_connect(123, "alice")

    assert build_calls == [(123, "alice", callback_url)]
    assert telegram.sent_message_payloads == [
        (
            123,
            GmailMessagesV2.Connect.CONNECT_PROMPT,
            {
                "inline_keyboard": [
                    [
                        {
                            "text": GmailButtons.GMAIL_CONNECT_INLINE,
                            "url": authorization_url,
                        },
                        {
                            "text": "🏠 Домой",
                            "callback_data": "🏠 Домой",
                        },
                    ],
                ]
            },
        )
    ]
    assert "Open this URL" not in telegram.sent_messages[0]
    assert authorization_url not in telegram.sent_messages[0]
