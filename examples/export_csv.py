"""Search hotels for fixed dates and export them to a CSV file.

Run:
    export SCRAPEUNBLOCKER_KEY=your_key_here
    python examples/export_csv.py
"""

from skyscanner_hotels import SkyscannerHotels
from skyscanner_hotels.scraper import write_csv


def main() -> None:
    scraper = SkyscannerHotels(market="UK", locale="en-GB", currency="GBP")
    hotels = scraper.search(
        "London",
        checkin="2026-10-15",
        checkout="2026-10-17",
        adults=2,
        rooms=1,
        max_results=50,
    )

    path = write_csv(hotels, "london_hotels.csv")
    print(f"Wrote {len(hotels)} hotels to {path}")


if __name__ == "__main__":
    main()
