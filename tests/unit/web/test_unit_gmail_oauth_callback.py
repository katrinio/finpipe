import pytest
from fastapi.testclient import TestClient

from src.integrations.gmail.exceptions import GmailOAuthError
from src.interfaces.web.app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _no_audit(monkeypatch) -> None:
    import src.interfaces.web.routes.gmail_oauth as _route_module

    monkeypatch.setattr(_route_module, "_audit", lambda **_kwargs: None)


def test_callback_route_returns_success_page(monkeypatch) -> None:
    monkeypatch.setattr("src.interfaces.web.routes.gmail_oauth.GmailOAuthSettings.is_callback_enabled", lambda: True)
    monkeypatch.setattr(
        "src.interfaces.web.routes.gmail_oauth.GmailOAuthCallbackService.handle_callback",
        lambda **kwargs: type("Result", (), {"ok": True, "message": "ok", "telegram_id": 123})(),
    )

    response = client.get("/oauth/gmail/callback?code=abc&state=state-1")

    assert response.status_code == 200
    assert "Gmail successfully connected." in response.text


def test_callback_route_returns_error_page_on_missing_code(monkeypatch) -> None:
    monkeypatch.setattr("src.interfaces.web.routes.gmail_oauth.GmailOAuthSettings.is_callback_enabled", lambda: True)

    response = client.get("/oauth/gmail/callback?state=state-1")

    assert response.status_code == 400
    assert "Gmail connection failed." in response.text
    assert "Missing code" in response.text


def test_callback_route_returns_error_page_on_missing_state(monkeypatch) -> None:
    monkeypatch.setattr("src.interfaces.web.routes.gmail_oauth.GmailOAuthSettings.is_callback_enabled", lambda: True)

    response = client.get("/oauth/gmail/callback?code=abc")

    assert response.status_code == 400
    assert "Missing state" in response.text


def test_callback_route_returns_error_page_on_oauth_error(monkeypatch) -> None:
    monkeypatch.setattr("src.interfaces.web.routes.gmail_oauth.GmailOAuthSettings.is_callback_enabled", lambda: True)

    response = client.get("/oauth/gmail/callback?state=state-1&error=access_denied")

    assert response.status_code == 400
    assert "OAuth error: access_denied" in response.text


def test_callback_route_returns_error_page_on_invalid_state(monkeypatch) -> None:
    monkeypatch.setattr("src.interfaces.web.routes.gmail_oauth.GmailOAuthSettings.is_callback_enabled", lambda: True)
    monkeypatch.setattr(
        "src.interfaces.web.routes.gmail_oauth.GmailOAuthCallbackService.handle_callback",
        lambda **kwargs: (_ for _ in ()).throw(GmailOAuthError("Invalid OAuth state")),
    )

    response = client.get("/oauth/gmail/callback?code=abc&state=state-1")

    assert response.status_code == 400
    assert "Invalid OAuth state" in response.text


def test_callback_route_returns_error_page_on_service_exception(monkeypatch) -> None:
    monkeypatch.setattr("src.interfaces.web.routes.gmail_oauth.GmailOAuthSettings.is_callback_enabled", lambda: True)
    monkeypatch.setattr(
        "src.interfaces.web.routes.gmail_oauth.GmailOAuthCallbackService.handle_callback",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.get("/oauth/gmail/callback?code=abc&state=state-1")

    assert response.status_code == 400
    assert "Internal callback error." in response.text
