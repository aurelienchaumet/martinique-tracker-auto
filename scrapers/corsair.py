from typing import Optional

from playwright.async_api import Page
from playwright_stealth import stealth_async

from scrapers.base import AirlineScraper

# Selectors identified by inspecting https://www.corsair.fr
# Update these if the site structure changes
_PRICE_SELECTOR = ".price-amount, .total-price, [data-price], .fare-amount"
_RESULTS_SELECTOR = ".results-container, .flight-list, .offers-list"


class CorsairScraper(AirlineScraper):
    name = "Corsair"
    _BASE_URL = "https://www.corsair.fr"

    async def _fetch_price(self, page: Page, outbound: str, return_date: str) -> Optional[float]:
        await stealth_async(page)
        await page.goto(self._BASE_URL, wait_until="networkidle", timeout=30000)
        await self._random_delay()

        await page.fill("[name='origin'], [id*='origin'], [placeholder*='Départ']", "ORY")
        await self._random_delay()

        await page.fill("[name='destination'], [id*='destination'], [placeholder*='Destination']", "FDF")
        await self._random_delay()

        d_out = self._fmt_date(outbound)
        await page.fill("[name='departDate'], [id*='depart'], [placeholder*='Aller']", d_out)

        d_ret = self._fmt_date(return_date)
        await page.fill("[name='returnDate'], [id*='retour'], [placeholder*='Retour']", d_ret)

        await page.click("button[type='submit'], .btn-search, #searchFlights")
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
