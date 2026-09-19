"""Unit tests for the parsing/shaping layer."""

from __future__ import annotations

from skyscanner_hotels.models import CSV_FIELDS, parse_hotel


def test_parse_full_hotel(sample_payload):
    hotel = parse_hotel(sample_payload["hotels"][0], currency="GBP")

    assert hotel.id == "185206755"
    assert hotel.name == "Native Bankside"
    assert hotel.star_level == 4
    assert hotel.star_label == "4 stars"
    assert hotel.accommodation_type == "Homes and apartments"
    assert hotel.price_per_night == 173.5
    assert hotel.price_per_night_with_taxes == 173.64
    assert hotel.price_total == 347.0
    assert hotel.currency == "GBP"
    assert hotel.review_score == 4.5
    assert hotel.review_score_label == "Excellent"
    assert hotel.review_count == 680
    assert hotel.city == "London"
    assert hotel.latitude == 51.507519
    assert hotel.cheapest_partner == "Booking.com"
    assert hotel.booking_url.endswith("native-bankside")
    assert hotel.image == "https://content.skyscnr.com/available/1/1_WxH.jpg"
    assert len(hotel.images) == 2


def test_parse_sparse_hotel_is_defensive(sample_payload):
    """A hotel with no reviews/partners/coords must not raise and stays clean."""
    hotel = parse_hotel(sample_payload["hotels"][1], currency="USD")

    assert hotel.id == "999"  # coerced from int
    assert hotel.review_score is None
    assert hotel.review_count is None
    assert hotel.cheapest_partner is None
    assert hotel.booking_url is None
    assert hotel.city is None
    assert hotel.latitude is None
    assert hotel.image is None
    assert hotel.images == []
    assert hotel.price_per_night == 88.0
    # taxes-inclusive price was absent for this hotel
    assert hotel.price_per_night_with_taxes is None


def test_parse_empty_object_does_not_crash():
    hotel = parse_hotel({}, currency="USD")
    assert hotel.name is None
    assert hotel.images == []
    assert hotel.currency == "USD"


def test_to_row_matches_csv_fields(sample_payload):
    hotel = parse_hotel(sample_payload["hotels"][0], currency="GBP")
    row = hotel.to_row()
    assert list(row.keys()) == CSV_FIELDS
    assert "images" not in row  # the list column is intentionally excluded
