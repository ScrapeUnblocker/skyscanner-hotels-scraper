"""Unit tests for the HTTP client: retry/backoff and error handling (fully mocked)."""

from __future__ import annotations

import pytest
import requests

from skyscanner_hotels.client import (
    API_KEY_ENV,
    PluginError,
    RateLimitError,
    ScrapeUnblockerClient,
)


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.text = text

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


class FakeSession:
    """Returns queued responses (or raises queued exceptions) in order."""

    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.calls = []

    def post(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _client(session, **kw):
    return ScrapeUnblockerClient("test-key", session=session, backoff=0, **kw)


def test_requires_api_key(monkeypatch):
    monkeypatch.delenv(API_KEY_ENV, raising=False)
    with pytest.raises(PluginError, match="No API key"):
        ScrapeUnblockerClient(None)


def test_reads_key_from_env(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV, "env-key")
    client = ScrapeUnblockerClient()
    assert client.api_key == "env-key"


def test_success_sends_key_header_and_drops_none_params():
    session = FakeSession([FakeResponse(200, {"hotels": []})])
    client = _client(session)
    out = client.post("/hotels/skyscanner-quotes", {"destination": "London", "adults": None})
    assert out == {"hotels": []}
    assert session.calls[0]["headers"]["x-scrapeunblocker-key"] == "test-key"
    assert "adults" not in session.calls[0]["params"]  # None dropped


def test_retries_on_5xx_then_succeeds():
    session = FakeSession([FakeResponse(503, text="overloaded"), FakeResponse(200, {"ok": 1})])
    client = _client(session, max_retries=3)
    assert client.post("/x", {}) == {"ok": 1}
    assert len(session.calls) == 2


def test_retries_on_network_error_then_succeeds():
    session = FakeSession([requests.ConnectionError("boom"), FakeResponse(200, {"ok": 1})])
    client = _client(session, max_retries=3)
    assert client.post("/x", {}) == {"ok": 1}


def test_exhausted_retries_raises_ratelimit():
    session = FakeSession([FakeResponse(429, text="slow down")] * 3)
    client = _client(session, max_retries=2)
    with pytest.raises(RateLimitError) as exc:
        client.post("/x", {})
    assert exc.value.status_code == 429


def test_non_retryable_4xx_raises_immediately():
    session = FakeSession([FakeResponse(422, text="bad destination")])
    client = _client(session, max_retries=3)
    with pytest.raises(PluginError) as exc:
        client.post("/x", {})
    assert exc.value.status_code == 422
    assert len(session.calls) == 1  # no retry
