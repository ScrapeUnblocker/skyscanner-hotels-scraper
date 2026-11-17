# skyscanner-hotels

[![CI](https://github.com/ScrapeUnblocker/skyscanner-hotels-scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/ScrapeUnblocker/skyscanner-hotels-scraper/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Pull **live hotel quotes from Skyscanner** as clean, structured JSON — for any
destination and stay dates — with a tidy CLI and a small Python library.

> **Powered by [ScrapeUnblocker](https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos)** —
> this project calls the ScrapeUnblocker **Skyscanner Hotels** plugin, which handles
> the browser rendering, geo-routing and anti-bot layer for you and returns tidy JSON.

Skyscanner's own pages are heavy, JavaScript-rendered and aggressively bot-protected.
The plugin does the hard part; this package turns the deeply-nested response into a
flat `Hotel` record you can actually work with — name, star rating, per-night and
total price (with taxes), guest review score and count, accommodation type, address
and geolocation, the cheapest booking partner with a deep link, and images.

## Features

- 🏨 **Real hotel quotes** — per-night and total price, taxes-inclusive figures, currency
- ⭐ **Ratings** — star level/label plus guest review score, description and count
- 📍 **Location** — full address, city and latitude/longitude
- 🔗 **Cheapest partner + deep link** — jump straight to the booking page
- 🎛️ **Controls** — guests, rooms, market, locale, currency, result count
- 🔎 **Client-side filters** — minimum review score and star level
- 💾 **Export** — pretty JSON or CSV out of the box
- 🔁 **Resilient client** — automatic retries with backoff on transient errors
- 🧪 **Tested** — offline unit tests (mocked API, no credit spent) + CI on 3.11 and 3.13

## Install

```bash
pip install .
# or, for development (tests + linters):
pip install -e ".[dev]"
```

Set your API key (get one at
[scrapeunblocker.com](https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos)):

```bash
export SCRAPEUNBLOCKER_KEY=your_key_here      # Windows PowerShell: $env:SCRAPEUNBLOCKER_KEY="..."
```

There's a `.env.example` you can copy to `.env`.

## CLI usage

```bash
# Cheapest hotels in London for specific dates
skyscanner-hotels "London" --checkin 2027-05-12 --checkout 2027-05-14 --market UK --currency GBP

# Default to a 3-night stay 30 days out, keep only well-reviewed 4-star+ hotels
skyscanner-hotels "New York" --nights 3 --min-score 4 --min-stars 4

# Export to CSV
skyscanner-hotels "Barcelona" --max-results 100 --csv barcelona.csv

# Full JSON to stdout (pipe into jq, files, etc.)
skyscanner-hotels "Paris" --json > paris.json
```

Example output:

```
Hotel                                         Night      Total  Score  Reviews
------------------------------------------------------------------------------
Point A Hotel London Kings Cross                 96        192    4.2     3120
Native Bankside                                 174        347    4.5      680
The Z Hotel Piccadilly                          181        362    4.3     5210
------------------------------------------------------------------------------
35 hotels · prices in GBP
```

## Library usage

```python
from skyscanner_hotels import SkyscannerHotels

scraper = SkyscannerHotels(market="UK", locale="en-GB", currency="GBP")

hotels = scraper.search(
    "London",
    checkin="2027-05-12",
    checkout="2027-05-14",
    adults=2,
    rooms=1,
    max_results=50,
    min_score=4.0,  # optional client-side filters
)

for hotel in hotels:
    print(hotel.name, hotel.price_per_night, hotel.currency, hotel.review_score)

# Export helpers
from skyscanner_hotels.scraper import to_json, write_csv

write_csv(hotels, "london.csv")
print(to_json(hotels[:5]))
```

Each `Hotel` is a dataclass:

```json
{
  "id": "185206755",
  "name": "Native Bankside",
  "star_level": 4,
  "star_label": "4 stars",
  "accommodation_type": "Homes and apartments",
  "price_per_night": 173.5,
  "price_per_night_with_taxes": 173.64,
  "price_total": 347.0,
  "price_total_with_taxes": 347.27,
  "currency": "GBP",
  "review_score": 4.5,
  "review_score_label": "Excellent",
  "review_count": 680,
  "distance": "London Borough of Southwark, London",
  "address": "1 and 2 Bear Gardens, London, SE1 9ED, United Kingdom",
  "city": "London",
  "latitude": 51.507519,
  "longitude": -0.095847,
  "cheapest_partner": "Booking.com",
  "booking_url": "https://www.skyscanner.net/hotel_deeplink/...",
  "url": "https://www.skyscanner.net/hotels/.../ht-185206755",
  "image": "https://content.skyscnr.com/available/.../_WxH.jpg",
  "images": ["https://content.skyscnr.com/available/.../_WxH.jpg", "..."]
}
```

Fields the plugin omits for a given property (e.g. review score for a brand-new
listing, or coordinates) come back as `null` rather than raising.

## Project layout

```
src/skyscanner_hotels/
  __init__.py     package exports + version
  client.py       tiny retrying HTTP client for the ScrapeUnblocker plugin API
  models.py       the Hotel dataclass + payload → Hotel shaping
  scraper.py      SkyscannerHotels: search, filter, sort, JSON/CSV export
  cli.py          argparse command-line interface
examples/         runnable scripts: basic search, CSV export, top-rated
tests/            offline unit tests (mocked API — no credit spent)
```

## Development

```bash
make install   # editable install with dev extras
make lint      # ruff check
make format    # ruff format
make test      # pytest (all offline / mocked)
```

The test suite mocks the HTTP layer, so `make test` spends **zero** API credit and
runs without a key.

## How it works

`skyscanner-hotels` sends one request per search to the ScrapeUnblocker
`POST /hotels/skyscanner-quotes` plugin endpoint (parameters in the query string,
API key in the `x-scrapeunblocker-key` header). The plugin resolves the destination
via Skyscanner autosuggest, renders and queries the live results behind a real
browser, and returns structured JSON; this package flattens each hotel into a
`Hotel` record, applies any filters, sorts by price and exports.

## Links

- 🌐 Website: <https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos>
- 📚 Docs: <https://docs.scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos>

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 ScrapeUnblocker.

This project is an independent example integration and is not affiliated with or
endorsed by Skyscanner. Respect Skyscanner's terms of service and applicable laws
when using it.
