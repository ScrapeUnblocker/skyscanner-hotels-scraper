"""Unit tests for the SkyscannerHotels orchestration: params, filters, sort, export."""

from __future__ import annotations

import csv
import json
import re

from skyscanner_hotels import SkyscannerHotels
from skyscanner_hotels.scraper import to_json, write_csv


class StubClient:
    """Stands in for ScrapeUnblockerClient; records params, returns a fixed payload."""

    def __init__(self, payload):
        self.payload = payload
        self.last_path = None
        self.last_params = None
        self.closed = False

    def post(self, path, params):
        self.last_path = path
        self.last_params = params
        return self.payload

    def close(self):
        self.closed = True


def _scraper(payload, **kw):
    return SkyscannerHotels(client=StubClient(payload), **kw)


def test_search_builds_expected_params(sample_payload):
    scraper = _scraper(sample_payload, market="UK", locale="en-GB", currency="GBP")
    scraper.search("London", checkin="2026-10-15", checkout="2026-10-17", adults=3, rooms=2)

    params = scraper.client.last_params
    assert scraper.client.last_path == "/hotels/skyscanner-quotes"
    assert params["destination"] == "London"
    assert params["checkin"] == "2026-10-15"
    assert params["checkout"] == "2026-10-17"
    assert params["adults"] == 3
    assert params["rooms"] == 2
    assert params["market"] == "UK"
    assert params["currency"] == "GBP"


def test_search_defaults_dates_when_omitted(sample_payload):
    scraper = _scraper(sample_payload)
    scraper.search("London", nights=3)
    params = scraper.client.last_params
    assert re.match(r"\d{4}-\d{2}-\d{2}", params["checkin"])
    assert re.match(r"\d{4}-\d{2}-\d{2}", params["checkout"])
    assert params["checkin"] < params["checkout"]


def test_max_results_clamped(sample_payload):
    scraper = _scraper(sample_payload)
    scraper.search("London", max_results=5000)
    assert scraper.client.last_params["max_results"] == 300


def test_results_sorted_by_price_cheapest_first(sample_payload):
    scraper = _scraper(sample_payload)
    hotels = scraper.search("London")
    prices = [h.price_per_night for h in hotels]
    assert prices == [88.0, 173.5]


def test_min_score_filter(sample_payload):
    scraper = _scraper(sample_payload)
    hotels = scraper.search("London", min_score=4.0)
    assert [h.name for h in hotels] == ["Native Bankside"]


def test_min_stars_filter(sample_payload):
    scraper = _scraper(sample_payload)
    hotels = scraper.search("London", min_stars=1)
    assert [h.name for h in hotels] == ["Native Bankside"]


def test_to_json_roundtrip(sample_payload):
    scraper = _scraper(sample_payload)
    hotels = scraper.search("London")
    parsed = json.loads(to_json(hotels))
    assert len(parsed) == 2
    assert parsed[0]["currency"] == "USD"
    assert "images" in parsed[0]


def test_write_csv(tmp_path, sample_payload):
    scraper = _scraper(sample_payload)
    hotels = scraper.search("London")
    out = write_csv(hotels, tmp_path / "out.csv")
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 2
    assert rows[0]["name"] == "No-Frills Inn"
    assert "images" not in rows[0]  # list column excluded from CSV


def test_context_manager_closes_client(sample_payload):
    with _scraper(sample_payload) as scraper:
        client = scraper.client
    assert client.closed is True
