"""The clean ``Hotel`` record and helpers for turning the raw plugin payload into it."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# Column order used for CSV export and stable, predictable output.
CSV_FIELDS = [
    "id",
    "name",
    "star_level",
    "star_label",
    "accommodation_type",
    "price_per_night",
    "price_per_night_with_taxes",
    "price_total",
    "price_total_with_taxes",
    "currency",
    "review_score",
    "review_score_label",
    "review_count",
    "distance",
    "address",
    "city",
    "latitude",
    "longitude",
    "cheapest_partner",
    "booking_url",
    "url",
    "image",
]


@dataclass
class Hotel:
    """A single hotel quote, flattened from the Skyscanner plugin response."""

    id: str | None = None
    name: str | None = None
    star_level: int | None = None
    star_label: str | None = None
    accommodation_type: str | None = None
    price_per_night: float | None = None
    price_per_night_with_taxes: float | None = None
    price_total: float | None = None
    price_total_with_taxes: float | None = None
    currency: str | None = None
    review_score: float | None = None
    review_score_label: str | None = None
    review_count: int | None = None
    distance: str | None = None
    address: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    cheapest_partner: str | None = None
    booking_url: str | None = None
    url: str | None = None
    image: str | None = None
    images: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Full record, including the ``images`` list."""
        return asdict(self)

    def to_row(self) -> dict[str, Any]:
        """Flat record for CSV/tabular output (drops the ``images`` list)."""
        data = self.to_dict()
        return {key: data.get(key) for key in CSV_FIELDS}


def _first(mapping: Any, *keys: str) -> Any:
    """Return ``mapping[key]`` for the first present key, else ``None``."""
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def parse_hotel(raw: dict[str, Any], currency: str | None) -> Hotel:
    """Shape one raw hotel object from the plugin into a :class:`Hotel`.

    Defensive throughout: the plugin omits sections for some properties
    (no review summary, no partner offers, no coordinates), so every lookup
    tolerates missing/``None`` branches.
    """
    price = raw.get("cheapestPrice") or {}
    per_night = price.get("pricePerNight") or {}
    total = price.get("priceTotal") or {}

    review = raw.get("reviewSummary") or {}
    stars = raw.get("stars") or {}
    location = raw.get("location") or {}
    coords = location.get("coordinates") or {}

    images = [
        img.get("url")
        for img in (raw.get("images") or [])
        if isinstance(img, dict) and img.get("url")
    ]

    cheapest_partner, booking_url = _cheapest_offer(raw.get("partnerOffers") or [])

    return Hotel(
        id=_as_str(raw.get("id")),
        name=raw.get("name"),
        star_level=stars.get("level"),
        star_label=stars.get("label"),
        accommodation_type=(raw.get("accommodationTypeInfo") or {}).get("text"),
        price_per_night=_first(per_night, "displayPrice"),
        price_per_night_with_taxes=_first(per_night, "priceWithAllTaxes"),
        price_total=_first(total, "displayPrice"),
        price_total_with_taxes=_first(total, "priceWithAllTaxes"),
        currency=currency,
        review_score=review.get("score"),
        review_score_label=review.get("scoreDescription"),
        review_count=review.get("reviewCount"),
        distance=(raw.get("distance") or {}).get("distanceDescription"),
        address=location.get("address"),
        city=_city_name(location),
        latitude=coords.get("latitude"),
        longitude=coords.get("longitude"),
        cheapest_partner=cheapest_partner,
        booking_url=booking_url,
        url=raw.get("detailsPageUrl"),
        image=images[0] if images else None,
        images=images,
    )


def _cheapest_offer(partner_offers: list[Any]) -> tuple[str | None, str | None]:
    """Pull the partner name + deep link from the first partner offer, if any."""
    for entry in partner_offers:
        if not isinstance(entry, dict):
            continue
        partner = (entry.get("partner") or {}).get("name")
        offers = entry.get("offers") or []
        url = None
        for offer in offers:
            if isinstance(offer, dict) and offer.get("url"):
                url = offer["url"]
                break
        if partner or url:
            return partner, url
    return None, None


def _city_name(location: dict[str, Any]) -> str | None:
    for parent in location.get("parents") or []:
        if isinstance(parent, dict) and parent.get("type") == "City":
            return parent.get("name")
    return None


def _as_str(value: Any) -> str | None:
    return str(value) if value is not None else None
