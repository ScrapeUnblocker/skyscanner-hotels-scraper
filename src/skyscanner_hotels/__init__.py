"""skyscanner_hotels - pull live hotel quotes from Skyscanner as clean JSON.

Powered by the ScrapeUnblocker Skyscanner Hotels plugin
(https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=example-repos).

Typical usage::

    from skyscanner_hotels import SkyscannerHotels

    scraper = SkyscannerHotels()  # reads SCRAPEUNBLOCKER_KEY from the env
    hotels = scraper.search("London", checkin="2027-05-12", checkout="2027-05-14")
    for hotel in hotels:
        print(hotel.name, hotel.price_per_night, hotel.currency)
"""

from __future__ import annotations

from .client import PluginError, RateLimitError, ScrapeUnblockerClient
from .models import Hotel
from .scraper import SkyscannerHotels

__all__ = [
    "SkyscannerHotels",
    "Hotel",
    "ScrapeUnblockerClient",
    "PluginError",
    "RateLimitError",
]

__version__ = "0.1.0"
