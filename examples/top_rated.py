"""Find the best-reviewed 4-star-plus hotels and print them as JSON.

Run:
    export SCRAPEUNBLOCKER_KEY=your_key_here
    python examples/top_rated.py
"""

from skyscanner_hotels import SkyscannerHotels
from skyscanner_hotels.scraper import to_json


def main() -> None:
    scraper = SkyscannerHotels(currency="EUR", market="FR", locale="en-GB")
    hotels = scraper.search(
        "Paris",
        nights=2,
        max_results=100,
        min_score=4.0,
        min_stars=4,
    )

    # Re-sort by guest review score, highest first.
    hotels.sort(key=lambda h: h.review_score or 0, reverse=True)
    print(to_json(hotels[:5]))


if __name__ == "__main__":
    main()
