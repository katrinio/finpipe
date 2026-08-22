import logging

import pytest
from requests import Response
from requests.exceptions import ConnectionError

from src.infrastructure.http.http_client import HttpClient, HttpRequestError


def test_http_error_never_logs_or_raises_with_telegram_token(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    token = "123456:super-secret-token"
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    response = Response()
    response.status_code = 500
    response._content = b'{"ok": false}'
    response.url = url
    monkeypatch.setattr("src.infrastructure.http.http_client.requests.request", lambda *args, **kwargs: response)
    caplog.set_level(logging.DEBUG)

    with pytest.raises(HttpRequestError) as exc_info:
        HttpClient().post(url)

    assert token not in caplog.text
    assert token not in str(exc_info.value)
    assert "bot***/sendDocument" in caplog.text


def test_transport_error_never_logs_or_raises_with_telegram_token(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = "123456:super-secret-token"
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    def fail_request(*args: object, **kwargs: object) -> Response:
        raise ConnectionError(f"connection failed for {url}")

    monkeypatch.setattr("src.infrastructure.http.http_client.requests.request", fail_request)
    caplog.set_level(logging.DEBUG)

    with pytest.raises(HttpRequestError) as exc_info:
        HttpClient().post(url)

    assert token not in caplog.text
    assert token not in str(exc_info.value)
    assert "bot***/sendMessage" in caplog.text
