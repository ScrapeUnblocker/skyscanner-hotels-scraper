"""Search hotels and print a compact summary.

Run:
    export SCRAPEUNBLOCKER_KEY=your_key_here
    python examples/basic_search.py
"""

from skyscanner_hotels import SkyscannerHotels


def main() -> None:
    scraper = SkyscannerHotels(currency="USD")
    hotels = scraper.search("Barcelona", nights=3, max_results=15)

    print(f"Found {len(hotels)} hotels in Barcelona\n")
    for hotel in hotels[:10]:
        price = f"{hotel.price_per_night:.0f} {hotel.currency}" if hotel.price_per_night else "n/a"
        score = f"{hotel.review_score}/5" if hotel.review_score else "no reviews"
        print(f"- {hotel.name}  ({hotel.star_label})")
        print(f"    {price}/night · {score} · {hotel.distance}")
        print(f"    {hotel.url}")


if __name__ == "__main__":
    main()
