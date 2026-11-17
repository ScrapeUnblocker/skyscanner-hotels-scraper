"""A tiny, dependency-light HTTP client for the ScrapeUnblocker plugin API.

The official ``scrapeunblocker`` Python SDK also wraps this endpoint
(``Client().skyscanner.hotels(...)``); this module speaks to it directly with
``requests`` instead. The request contract is simple: a ``POST`` with all
parameters in the query string and the API key in the ``x-scrapeunblocker-key``
header.

Docs: https://docs.scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests

DEFAULT_BASE_URL = "https://api.scrapeunblocker.com"
API_KEY_ENV = "SCRAPEUNBLOCKER_KEY"

# Transient statuses worth retrying: rate limit + upstream gateway errors.
_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


class PluginError(RuntimeError):
    """Raised when the ScrapeUnblocker plugin API returns a non-recoverable error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(PluginError):
    """Raised when retries are exhausted against a rate-limited/overloaded endpoint."""


class ScrapeUnblockerClient:
    """Minimal client for ScrapeUnblocker plugin endpoints.

    Args:
        api_key: Your ScrapeUnblocker API key. Falls back to the
            ``SCRAPEUNBLOCKER_KEY`` environment variable.
        base_url: Override the API base URL (rarely needed).
        timeout: Per-request timeout in seconds.
        max_retries: How many times to retry transient failures.
        backoff: Base seconds for exponential backoff between retries.
        session: Optional pre-built ``requests.Session`` (handy for tests).
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 60.0,
        max_retries: int = 4,
        backoff: float = 1.5,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get(API_KEY_ENV)
        if not self.api_key:
            raise PluginError(
                f"No API key. Pass api_key=... or set the {API_KEY_ENV} environment variable. "
                "Get one at https://scrapeunblocker.com/"
                "?utm_source=github&utm_medium=integration&utm_campaign=example-repos"
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self._session = session or requests.Session()

    def post(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """POST to ``path`` with ``params`` in the query string, returning parsed JSON.

        Retries transient failures (429/5xx and network errors) with exponential
        backoff. ``None`` values in ``params`` are dropped.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        query = {k: v for k, v in params.items() if v is not None}
        headers = {"x-scrapeunblocker-key": self.api_key}

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self._session.post(url, params=query, headers=headers, timeout=self.timeout)
            except requests.RequestException as exc:  # network / timeout
                last_exc = exc
                if attempt < self.max_retries:
                    self._sleep(attempt)
                    continue
                raise PluginError(f"Request to {path} failed: {exc}") from exc

            if resp.status_code in _RETRY_STATUSES and attempt < self.max_retries:
                self._sleep(attempt)
                continue

            if resp.status_code >= 400:
                detail = _short_body(resp)
                if resp.status_code in _RETRY_STATUSES:
                    raise RateLimitError(
                        f"{path} still failing after {self.max_retries} retries "
                        f"(HTTP {resp.status_code}): {detail}",
                        status_code=resp.status_code,
                    )
                raise PluginError(
                    f"{path} returned HTTP {resp.status_code}: {detail}",
                    status_code=resp.status_code,
                )

            try:
                return resp.json()
            except ValueError as exc:
                raise PluginError(f"{path} returned non-JSON response") from exc

        # Only reachable if every attempt raised a network error.
        raise PluginError(f"Request to {path} failed: {last_exc}")

    def _sleep(self, attempt: int) -> None:
        time.sleep(self.backoff * (2**attempt))

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> ScrapeUnblockerClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def _short_body(resp: requests.Response, limit: int = 300) -> str:
    text = (resp.text or "").strip().replace("\n", " ")
    return text[:limit] if text else "<empty body>"
