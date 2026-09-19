"""High-level ``SkyscannerHotels`` scraper: search, shape, filter and export."""

from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .client import ScrapeUnblockerClient
from .models import CSV_FIELDS, Hotel, parse_hotel

HOTELS_PATH = "/hotels/skyscanner-quotes"

# The plugin returns roughly 35 results per page and caps out around 300.
MAX_RESULTS_CAP = 300


class SkyscannerHotels:
    """Search Skyscanner hotel quotes and get back clean :class:`Hotel` records.

    Args:
        api_key: ScrapeUnblocker API key (falls back to ``SCRAPEUNBLOCKER_KEY``).
        market: Skyscanner market code, e.g. ``US``, ``UK``, ``DE``.
        locale: Language/locale, e.g. ``en-US``.
        currency: ISO currency code for prices, e.g. ``USD``.
        client: Optional pre-built :class:`ScrapeUnblockerClient` (used in tests).
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        market: str = "US",
        locale: str = "en-US",
        currency: str = "USD",
        client: ScrapeUnblockerClient | None = None,
    ) -> None:
        self.market = market
        self.locale = locale
        self.currency = currency
        self.client = client or ScrapeUnblockerClient(api_key)

    def search(
        self,
        destination: str,
        *,
        checkin: str | None = None,
        checkout: str | None = None,
        nights: int = 2,
        adults: int = 2,
        rooms: int = 1,
        max_results: int = 35,
        min_score: float | None = None,
        min_stars: int | None = None,
    ) -> list[Hotel]:
        """Search hotels in ``destination`` for the given stay.

        Args:
            destination: City or place name (resolved by Skyscanner autosuggest),
                e.g. ``"London"`` or ``"New York"``.
            checkin/checkout: ``YYYY-MM-DD`` dates. If omitted, defaults to a
                ``nights``-long stay starting 30 days from today.
            nights: Stay length used only when ``checkin``/``checkout`` are omitted.
            adults: Guest count.
            rooms: Room count.
            max_results: Desired result count (clamped to {cap}).
            min_score: Keep only hotels with a guest review score >= this.
            min_stars: Keep only hotels with a star level >= this.

        Returns:
            A list of :class:`Hotel`, sorted by price-per-night (cheapest first,
            missing prices last).
        """
        checkin, checkout = _resolve_dates(checkin, checkout, nights)
        params: dict[str, Any] = {
            "destination": destination,
            "checkin": checkin,
            "checkout": checkout,
            "adults": adults,
            "rooms": rooms,
            "market": self.market,
            "locale": self.locale,
            "currency": self.currency,
            "max_results": min(max_results, MAX_RESULTS_CAP),
        }
        payload = self.client.post(HOTELS_PATH, params)
        hotels = [parse_hotel(raw, self.currency) for raw in payload.get("hotels") or []]

        if min_score is not None:
            hotels = [h for h in hotels if (h.review_score or 0) >= min_score]
        if min_stars is not None:
            hotels = [h for h in hotels if (h.star_level or 0) >= min_stars]

        hotels.sort(key=lambda h: (h.price_per_night is None, h.price_per_night or 0.0))
        return hotels

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> SkyscannerHotels:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


# search() docstring interpolation for the cap.
SkyscannerHotels.search.__doc__ = (SkyscannerHotels.search.__doc__ or "").format(
    cap=MAX_RESULTS_CAP
)


def _resolve_dates(checkin: str | None, checkout: str | None, nights: int) -> tuple[str, str]:
    if checkin and checkout:
        return checkin, checkout
    start = date.today() + timedelta(days=30)
    end = start + timedelta(days=max(1, nights))
    return checkin or start.isoformat(), checkout or end.isoformat()


def to_json(hotels: list[Hotel], *, indent: int = 2) -> str:
    """Serialize hotels to a JSON array string (full records, incl. images)."""
    return json.dumps([h.to_dict() for h in hotels], indent=indent, ensure_ascii=False)


def write_csv(hotels: list[Hotel], path: str | Path) -> Path:
    """Write hotels to a CSV file and return the path."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for hotel in hotels:
            writer.writerow(hotel.to_row())
    return out
