import pytest
from unittest.mock import MagicMock, patch
from scrapers.google_flights import (
    GoogleFlightsScraper,
    _parse_price_eur,
    _normalize_airline,
)


# --- _parse_price_eur ---

def test_parse_price_eur_euros():
    assert _parse_price_eur("487 €", 0.93) == 487.0


def test_parse_price_eur_thousands_space():
    assert _parse_price_eur("1 234 €", 0.93) == 1234.0


def test_parse_price_eur_decimal_comma():
    assert _parse_price_eur("1 234,50 €", 0.93) == 1234.5


def test_parse_price_eur_usd_converts():
    assert _parse_price_eur("$2000", 0.93) == round(2000 * 0.93, 2)


def test_parse_price_eur_usd_with_spaces():
    assert _parse_price_eur("$1 965", 0.93) == round(1965 * 0.93, 2)


def test_parse_price_eur_invalid():
    assert _parse_price_eur("non disponible", 0.93) is None


def test_parse_price_eur_empty():
    assert _parse_price_eur("", 0.93) is None


# --- _normalize_airline ---

def test_normalize_air_france():
    assert _normalize_airline("Air France") == "Air France"
    assert _normalize_airline("AIR FRANCE") == "Air France"


def test_normalize_air_caraibes():
    assert _normalize_airline("Air Caraïbes") == "Air Caraïbes"
    assert _normalize_airline("Air Caraibes") == "Air Caraïbes"


def test_normalize_corsair():
    assert _normalize_airline("Corsair") == "Corsair"
    assert _normalize_airline("CORSAIR International") == "Corsair"


def test_normalize_unknown_airline():
    assert _normalize_airline("Transavia") is None
    assert _normalize_airline("") is None


# --- Scraper ---

def _make_flight(name: str, price: str):
    f = MagicMock()
    f.name = name
    f.price = price
    return f


def test_get_prices_returns_three_airlines():
    scraper = GoogleFlightsScraper()
    mock_result = MagicMock()
    mock_result.flights = [
        _make_flight("Air France",   "$520"),
        _make_flight("Air Caraïbes", "$487"),
        _make_flight("Corsair",      "$399"),
        _make_flight("Transavia",    "$350"),  # filtré
    ]

    with patch("scrapers.google_flights.get_flights", return_value=mock_result), \
         patch("scrapers.google_flights._get_usd_to_eur", return_value=1.0):
        result = scraper.get_prices("2026-12-28", "2027-01-15")

    assert result == {"Air France": 520.0, "Air Caraïbes": 487.0, "Corsair": 399.0}
    assert "Transavia" not in result


def test_get_prices_converts_usd_to_eur():
    scraper = GoogleFlightsScraper()
    mock_result = MagicMock()
    mock_result.flights = [_make_flight("Corsair", "$2000")]

    with patch("scrapers.google_flights.get_flights", return_value=mock_result), \
         patch("scrapers.google_flights._get_usd_to_eur", return_value=0.93):
        result = scraper.get_prices("2026-12-28", "2027-01-15")

    assert result == {"Corsair": round(2000 * 0.93, 2)}


def test_get_prices_keeps_minimum_per_airline():
    scraper = GoogleFlightsScraper()
    mock_result = MagicMock()
    mock_result.flights = [
        _make_flight("Air France", "$550"),
        _make_flight("Air France", "$520"),
        _make_flight("Air France", "$610"),
    ]

    with patch("scrapers.google_flights.get_flights", return_value=mock_result), \
         patch("scrapers.google_flights._get_usd_to_eur", return_value=1.0):
        result = scraper.get_prices("2026-12-28", "2027-01-15")

    assert result == {"Air France": 520.0}


def test_get_prices_returns_empty_on_api_error():
    scraper = GoogleFlightsScraper()

    with patch("scrapers.google_flights.get_flights", side_effect=Exception("API error")):
        result = scraper.get_prices("2026-12-28", "2027-01-15")

    assert result == {}


def test_get_prices_returns_empty_on_empty_results():
    scraper = GoogleFlightsScraper()
    mock_result = MagicMock()
    mock_result.flights = []

    with patch("scrapers.google_flights.get_flights", return_value=mock_result), \
         patch("scrapers.google_flights._get_usd_to_eur", return_value=0.93):
        result = scraper.get_prices("2026-12-28", "2027-01-15")

    assert result == {}


def test_get_prices_returns_empty_when_no_result():
    scraper = GoogleFlightsScraper()

    with patch("scrapers.google_flights.get_flights", return_value=None):
        result = scraper.get_prices("2026-12-28", "2027-01-15")

    assert result == {}
