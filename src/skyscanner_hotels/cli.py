"""Command-line interface for skyscanner_hotels.

Examples::

    skyscanner-hotels "London" --checkin 2026-10-15 --checkout 2026-10-17
    skyscanner-hotels "New York" --nights 3 --min-score 4 --csv hotels.csv
"""

from __future__ import annotations

import argparse
import sys

from .client import PluginError
from .models import Hotel
from .scraper import SkyscannerHotels, to_json, write_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skyscanner-hotels",
        description="Pull live hotel quotes from Skyscanner via the ScrapeUnblocker plugin.",
    )
    parser.add_argument("destination", help='City or place name, e.g. "London" or "New York".')
    parser.add_argument("--checkin", help="Check-in date, YYYY-MM-DD.")
    parser.add_argument("--checkout", help="Check-out date, YYYY-MM-DD.")
    parser.add_argument(
        "--nights", type=int, default=2, help="Stay length if dates omitted (default: 2)."
    )
    parser.add_argument("--adults", type=int, default=2, help="Guest count (default: 2).")
    parser.add_argument("--rooms", type=int, default=1, help="Room count (default: 1).")
    parser.add_argument(
        "--max-results", type=int, default=35, help="Number of hotels to fetch (default: 35)."
    )
    parser.add_argument("--min-score", type=float, help="Keep hotels with review score >= this.")
    parser.add_argument("--min-stars", type=int, help="Keep hotels with star level >= this.")
    parser.add_argument("--market", default="US", help="Skyscanner market code (default: US).")
    parser.add_argument("--locale", default="en-US", help="Locale (default: en-US).")
    parser.add_argument("--currency", default="USD", help="Currency code (default: USD).")
    parser.add_argument("--csv", metavar="PATH", help="Write results to a CSV file.")
    parser.add_argument(
        "--json", action="store_true", help="Print full JSON instead of a summary table."
    )
    parser.add_argument("--api-key", help="API key (else read SCRAPEUNBLOCKER_KEY from env).")
    return parser


def _print_table(hotels: list[Hotel], currency: str) -> None:
    if not hotels:
        print("No hotels found.")
        return
    print(f"{'Hotel':<40} {'Night':>10} {'Total':>10} {'Score':>6} {'Reviews':>8}")
    print("-" * 78)
    for h in hotels:
        name = (h.name or "")[:38]
        night = f"{h.price_per_night:.0f}" if h.price_per_night is not None else "-"
        total = f"{h.price_total:.0f}" if h.price_total is not None else "-"
        score = f"{h.review_score:.1f}" if h.review_score is not None else "-"
        reviews = str(h.review_count) if h.review_count is not None else "-"
        print(f"{name:<40} {night:>10} {total:>10} {score:>6} {reviews:>8}")
    print("-" * 78)
    print(f"{len(hotels)} hotels · prices in {currency}")


def _force_utf8_stdout() -> None:
    """Print UTF-8 regardless of the console codepage (e.g. Windows cp1252),
    so non-Latin hotel names never raise UnicodeEncodeError."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdout()
    args = build_parser().parse_args(argv)
    try:
        scraper = SkyscannerHotels(
            api_key=args.api_key,
            market=args.market,
            locale=args.locale,
            currency=args.currency,
        )
        hotels = scraper.search(
            args.destination,
            checkin=args.checkin,
            checkout=args.checkout,
            nights=args.nights,
            adults=args.adults,
            rooms=args.rooms,
            max_results=args.max_results,
            min_score=args.min_score,
            min_stars=args.min_stars,
        )
    except PluginError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.csv:
        path = write_csv(hotels, args.csv)
        print(f"Wrote {len(hotels)} hotels to {path}")
    if args.json:
        print(to_json(hotels))
    elif not args.csv:
        _print_table(hotels, args.currency)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
