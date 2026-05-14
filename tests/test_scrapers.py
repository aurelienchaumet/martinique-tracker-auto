import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from scrapers.air_caraibes import AirCaraibesScraper


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    async def instant_sleep(_):
        pass
    monkeypatch.setattr(asyncio, "sleep", instant_sleep)


@pytest.mark.asyncio
async def test_air_caraibes_returns_float_on_success():
    scraper = AirCaraibesScraper()
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_element = AsyncMock()
    mock_element.inner_text = AsyncMock(return_value="487 €")
    mock_page.query_selector = AsyncMock(return_value=mock_element)

    price = await scraper.get_price(mock_page, "2026-12-28", "2027-01-15")
    assert isinstance(price, float)
    assert price == 487.0


@pytest.mark.asyncio
async def test_scraper_returns_none_on_timeout():
    scraper = AirCaraibesScraper()
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))

    price = await scraper.get_price(mock_page, "2026-12-28", "2027-01-15")
    assert price is None


@pytest.mark.asyncio
async def test_parse_price_strips_non_numeric():
    scraper = AirCaraibesScraper()
    assert scraper._parse_price("  487 €  ") == 487.0
    assert scraper._parse_price("1 234,50 €") == 1234.50
    assert scraper._parse_price("invalid") is None


@pytest.mark.asyncio
async def test_corsair_returns_none_on_missing_element():
    from scrapers.corsair import CorsairScraper
    scraper = CorsairScraper()
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.query_selector = AsyncMock(return_value=None)

    price = await scraper.get_price(mock_page, "2026-12-28", "2027-01-15")
    assert price is None


@pytest.mark.asyncio
async def test_air_france_parse_price():
    from scrapers.air_france import AirFranceScraper
    scraper = AirFranceScraper()
    assert scraper._parse_price("1 234 €") == 1234.0
    assert scraper._parse_price("€ 520,00") == 520.0
