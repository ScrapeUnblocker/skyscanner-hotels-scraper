"""Unit tests for the CLI argument parser and command flow (mocked scraper)."""

from __future__ import annotations

import json

import pytest

from skyscanner_hotels import cli
from skyscanner_hotels.client import PluginError
from skyscanner_hotels.models import parse_hotel


def test_parser_defaults():
    args = cli.build_parser().parse_args(["London"])
    assert args.destination == "London"
    assert args.adults == 2
    assert args.rooms == 1
    assert args.max_results == 35
    assert args.market == "US"


def test_parser_full():
    args = cli.build_parser().parse_args(
        [
            "New York",
            "--checkin",
            "2026-10-15",
            "--checkout",
            "2026-10-17",
            "--adults",
            "4",
            "--min-score",
            "4.2",
            "--csv",
            "out.csv",
            "--json",
        ]
    )
    assert args.adults == 4
    assert args.min_score == 4.2
    assert args.csv == "out.csv"
    assert args.json is True


@pytest.fixture
def patched_search(monkeypatch, sample_payload):
    """Patch SkyscannerHotels so main() runs without any network/key."""
    hotels = [parse_hotel(h, "USD") for h in sample_payload["hotels"]]

    class FakeScraper:
        def __init__(self, *a, **k):
            pass

        def search(self, *a, **k):
            return hotels

    monkeypatch.setattr(cli, "SkyscannerHotels", FakeScraper)
    return hotels


def test_main_table_output(patched_search, capsys):
    rc = cli.main(["London"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Native Bankside" in out
    assert "hotels" in out


def test_main_json_output(patched_search, capsys):
    rc = cli.main(["London", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 2


def test_main_csv_output(patched_search, capsys, tmp_path):
    dest = tmp_path / "hotels.csv"
    rc = cli.main(["London", "--csv", str(dest)])
    assert rc == 0
    assert dest.exists()
    assert "Wrote 2 hotels" in capsys.readouterr().out


def test_main_handles_plugin_error(monkeypatch, capsys):
    class BoomScraper:
        def __init__(self, *a, **k):
            pass

        def search(self, *a, **k):
            raise PluginError("bad destination", status_code=422)

    monkeypatch.setattr(cli, "SkyscannerHotels", BoomScraper)
    rc = cli.main(["Nowhere"])
    assert rc == 1
    assert "Error:" in capsys.readouterr().err
