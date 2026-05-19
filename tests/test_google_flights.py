import pytest
from unittest.mock import AsyncMock
from scrapers.google_flights import (
    GoogleFlightsScraper,
    _parse_price,
    _normalize_airline,
    _build_search_url,
)


# --- Fonctions utilitaires ---

def test_parse_price_integer():
    assert _parse_price("487 €") == 487.0


def test_parse_price_thousands_space():
    assert _parse_price("1 234 €") == 1234.0


def test_parse_price_decimal_comma():
    assert _parse_price("1 234,50 €") == 1234.5


def test_parse_price_invalid():
    assert _parse_price("non disponible") is None


def test_parse_price_empty():
    assert _parse_price("") is None


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


def test_build_search_url_contains_route_and_dates():
    url = _build_search_url("2026-12-28", "2027-01-15")
    assert "ORY" in url
    assert "FDF" in url
    assert "2026-12-28" in url
    assert "2027-01-15" in url


# --- Scraper ---

@pytest.mark.asyncio
async def test_get_prices_returns_three_airlines():
    scraper = GoogleFlightsScraper()
    mock_page = AsyncMock()
    mock_page.evaluate = AsyncMock(return_value=[
        {"airline": "Air France", "price": "520 €"},
        {"airline": "Air Caraïbes", "price": "487 €"},
        {"airline": "Corsair", "price": "399 €"},
        {"airline": "Transavia", "price": "350 €"},  # doit être filtré
    ])

    result = await scraper.get_prices(mock_page, "2026-12-28", "2027-01-15")

    assert result == {"Air France": 520.0, "Air Caraïbes": 487.0, "Corsair": 399.0}
    assert "Transavia" not in result


@pytest.mark.asyncio
async def test_get_prices_keeps_minimum_per_airline():
    scraper = GoogleFlightsScraper()
    mock_page = AsyncMock()
    mock_page.evaluate = AsyncMock(return_value=[
        {"airline": "Air France", "price": "550 €"},
        {"airline": "Air France", "price": "520 €"},
        {"airline": "Air France", "price": "610 €"},
    ])

    result = await scraper.get_prices(mock_page, "2026-12-28", "2027-01-15")
    assert result == {"Air France": 520.0}


@pytest.mark.asyncio
async def test_get_prices_returns_empty_on_navigation_error():
    scraper = GoogleFlightsScraper()
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock(side_effect=Exception("net::ERR_CONNECTION_REFUSED"))

    result = await scraper.get_prices(mock_page, "2026-12-28", "2027-01-15")
    assert result == {}


@pytest.mark.asyncio
async def test_get_prices_returns_empty_on_selector_timeout():
    scraper = GoogleFlightsScraper()
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout 30000ms exceeded"))

    result = await scraper.get_prices(mock_page, "2026-12-28", "2027-01-15")
    assert result == {}


@pytest.mark.asyncio
async def test_get_prices_returns_empty_on_empty_dom():
    scraper = GoogleFlightsScraper()
    mock_page = AsyncMock()
    mock_page.evaluate = AsyncMock(return_value=[])

    result = await scraper.get_prices(mock_page, "2026-12-28", "2027-01-15")
    assert result == {}
