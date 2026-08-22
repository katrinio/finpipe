"""Единая точка выполнения HTTP-запросов проекта."""

import logging
import re
from collections.abc import Mapping
from typing import Any

import requests
from requests import Response
from requests.exceptions import RequestException

LOGGER = logging.getLogger(__name__)
# Telegram authenticates in the URL path. Prevent the underlying transport from
# emitting that path even when another entry point enables global DEBUG logging.
logging.getLogger("urllib3").setLevel(logging.WARNING)
TELEGRAM_BOT_URL_PATTERN = re.compile(r"^(https://api\.telegram\.org/(?:file/)?bot)([^/]+)(/.*)?$")


class HttpRequestError(RuntimeError):
    """HTTP-запрос завершился ошибкой без раскрытия чувствительного URL."""


class HttpClient:
    """Выполняет HTTP-запросы с единым timeout, логированием и raise_for_status."""

    DEFAULT_TIMEOUT = 30

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: int | float | None = None,
    ) -> Response:
        """Выполняет HTTP GET."""

        return self._request("GET", url, params=params, headers=headers, timeout=timeout)

    def post(
        self,
        url: str,
        *,
        params: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
        json: Any = None,
        data: Mapping[str, object] | None = None,
        files: Mapping[str, object] | None = None,
        timeout: int | float | None = None,
    ) -> Response:
        """Выполняет HTTP POST."""

        return self._request(
            "POST",
            url,
            params=params,
            headers=headers,
            json=json,
            data=data,
            files=files,
            timeout=timeout,
        )

    def put(
        self,
        url: str,
        *,
        params: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
        json: Any = None,
        data: Mapping[str, object] | None = None,
        timeout: int | float | None = None,
    ) -> Response:
        """Выполняет HTTP PUT."""

        return self._request("PUT", url, params=params, headers=headers, json=json, data=data, timeout=timeout)

    def delete(
        self,
        url: str,
        *,
        params: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: int | float | None = None,
    ) -> Response:
        """Выполняет HTTP DELETE."""

        return self._request("DELETE", url, params=params, headers=headers, timeout=timeout)

    def _request(
        self,
        method: str,
        url: str,
        *,
        timeout: int | float | None = None,
        **kwargs: Any,
    ) -> Response:
        """Выполняет запрос и централизованно применяет базовые HTTP-правила."""

        safe_url = self._redact_url(url)
        LOGGER.debug("HTTP %s %s", method, safe_url)
        try:
            response = requests.request(method, url, timeout=timeout or self.DEFAULT_TIMEOUT, **kwargs)
        except RequestException as error:
            LOGGER.error("HTTP %s %s failed: %s", method, safe_url, type(error).__name__)
            raise HttpRequestError(f"HTTP {method} request failed for {safe_url}") from None
        if not response.ok:
            LOGGER.error("HTTP %s %s failed with status %s", method, safe_url, response.status_code)
        try:
            response.raise_for_status()
        except RequestException:
            raise HttpRequestError(f"HTTP {method} request failed for {safe_url} with status {response.status_code}") from None
        return response

    @staticmethod
    def _redact_url(url: str) -> str:
        """Скрывает секреты из URL, которые могут попасть в логи."""

        match = TELEGRAM_BOT_URL_PATTERN.match(url)
        if match is None:
            return url

        prefix, _token, suffix = match.groups()
        return f"{prefix}***{suffix or ''}"
