"""Единая точка выполнения HTTP-запросов проекта."""

import logging
from collections.abc import Mapping
from typing import Any

import requests
from requests import Response

LOGGER = logging.getLogger(__name__)


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

        LOGGER.info("HTTP %s %s", method, url)
        response = requests.request(method, url, timeout=timeout or self.DEFAULT_TIMEOUT, **kwargs)
        if not response.ok:
            LOGGER.error("HTTP %s %s\nResponse: %s", method, url, response.text)
        response.raise_for_status()
        return response
