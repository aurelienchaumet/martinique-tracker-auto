from typing import Optional

from playwright.async_api import Page
from playwright_stealth import stealth_async

from scrapers.base import AirlineScraper

_PRICE_SELECTOR = ".price-lowest, [data-testid='lowest-price'], .fare-price"
_RESULTS_SELECTOR = ".flight-results, .search-results"


class AirCaraibesScraper(AirlineScraper):
    name = "Air Caraïbes"
    _BASE_URL = "https://www.aircaribes.com"

    async def _fetch_price(self, page: Page, outbound: str, return_date: str) -> Optional[float]:
        await stealth_async(page)
        await page.goto(self._BASE_URL, wait_until="networkidle", timeout=30000)
        await self._random_delay()

        await page.fill("[name='origin'], [placeholder*='Départ'], #origin", "ORY")
        await self._random_delay()

        await page.fill("[name='destination'], [placeholder*='Destination'], #destination", "FDF")
        await self._random_delay()

        d_out = self._fmt_date(outbound)
        await page.fill("[name='departureDate'], [placeholder*='Aller'], #departureDate", d_out)

        d_ret = self._fmt_date(return_date)
        await page.fill("[name='returnDate'], [placeholder*='Retour'], #returnDate", d_ret)

        await page.click("button[type='submit'], .search-button, #searchBtn")
        await page.wait_for_selector(_RESULTS_SELECTOR, timeout=30000)
        await self._random_delay()

        element = await page.query_selector(_PRICE_SELECTOR)
        if not element:
            return None

        text = await element.inner_text()
        return self._parse_price(text)

    @staticmethod
    def _fmt_date(iso: str) -> str:
        y, m, d = iso.split("-")
        return f"{d}/{m}/{y}"
