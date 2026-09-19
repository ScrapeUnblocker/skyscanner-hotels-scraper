"""Shared fixtures: a realistic (trimmed) sample of the plugin response."""

from __future__ import annotations

import pytest

# Shaped after a real /hotels/skyscanner-quotes payload, trimmed to the fields
# the scraper reads, and deliberately including edge cases:
#  - hotel 2 has no review summary, no partner offers and no coordinates
SAMPLE_PAYLOAD = {
    "hotels": [
        {
            "id": "185206755",
            "name": "Native Bankside",
            "stars": {"level": 4, "label": "4 stars"},
            "distance": {"distanceDescription": "London Borough of Southwark, London"},
            "detailsPageUrl": "https://www.skyscanner.net/hotels/london/native-bankside/ht-185206755",
            "images": [
                {"url": "https://content.skyscnr.com/available/1/1_WxH.jpg"},
                {"url": "https://content.skyscnr.com/available/2/2_WxH.jpg"},
            ],
            "reviewSummary": {"score": 4.5, "scoreDescription": "Excellent", "reviewCount": 680},
            "cheapestPrice": {
                "pricePerNight": {"displayPrice": 173.5, "priceWithAllTaxes": 173.64},
                "priceTotal": {"displayPrice": 347.0, "priceWithAllTaxes": 347.27},
            },
            "location": {
                "address": "1 Bear Gardens, London, SE1 9ED, United Kingdom",
                "coordinates": {"latitude": 51.507519, "longitude": -0.095847},
                "parents": [
                    {"type": "Nation", "name": "United Kingdom"},
                    {"type": "City", "name": "London"},
                ],
            },
            "accommodationTypeInfo": {"text": "Homes and apartments"},
            "partnerOffers": [
                {
                    "partner": {"name": "Booking.com"},
                    "offers": [
                        {"url": "https://www.skyscanner.net/hotel_deeplink/native-bankside"}
                    ],
                }
            ],
        },
        {
            "id": 999,
            "name": "No-Frills Inn",
            "stars": {"level": 0, "label": "No stars"},
            "detailsPageUrl": "https://www.skyscanner.net/hotels/london/no-frills/ht-999",
            "images": [],
            "cheapestPrice": {
                "pricePerNight": {"displayPrice": 88.0},
                "priceTotal": {"displayPrice": 176.0},
            },
            "location": {"address": "Somewhere, London"},
        },
    ]
}


@pytest.fixture
def sample_payload() -> dict:
    return SAMPLE_PAYLOAD
