"""Search hotels for explicit stay dates and export them to a CSV file.

Run:
    export SCRAPEUNBLOCKER_KEY=your_key_here
    python examples/export_csv.py
"""

from datetime import date, timedelta

from skyscanner_hotels import SkyscannerHotels
from skyscanner_hotels.scraper import write_csv


def main() -> None:
    # A two-night stay a month out, so the example never searches a past date.
    checkin = date.today() + timedelta(days=30)
    checkout = checkin + timedelta(days=2)

    scraper = SkyscannerHotels(market="UK", locale="en-GB", currency="GBP")
    hotels = scraper.search(
        "London",
        checkin=checkin.isoformat(),
        checkout=checkout.isoformat(),
        adults=2,
        rooms=1,
        max_results=50,
    )

    path = write_csv(hotels, "london_hotels.csv")
    print(f"Wrote {len(hotels)} hotels to {path}")


if __name__ == "__main__":
    main()
