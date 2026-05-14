from typing import Optional

from playwright.async_api import Page
from playwright_stealth import stealth_async

from scrapers.base import AirlineScraper

# Selectors identified by inspecting https://www.airfrance.fr
# Air France SPA — selectors may require longer waits
_PRICE_SELECTOR = "[data-testid='price'], .price-value, .af-price, .fareAmount"
_RESULTS_SELECTOR = "[data-testid='flight-results'], .results, .flights-list"
_SEARCH_URL = (
    "https://www.airfrance.fr/FR/fr/local/process/achat/selectoffresvol.do"
    "?origin={origin}&destination={destination}"
    "&departureDate={outbound}&returnDate={return_date}"
    "&cabinClass=ECONOMY&passengerCount=1&tripType=R"
)


class AirFranceScraper(AirlineScraper):
    name = "Air France"

    async def _fetch_price(self, page: Page, outbound: str, return_date: str) -> Optional[float]:
        await stealth_async(page)

        url = _SEARCH_URL.format(
            origin="ORY",
            destination="FDF",
            outbound=outbound,
            return_date=return_date,
        )
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await self._random_delay()

        try:
            await page.wait_for_selector(_RESULTS_SELECTOR, timeout=30000)
        except Exception:
            return await self._fetch_via_form(page, outbound, return_date)

        await self._random_delay()
        element = await page.query_selector(_PRICE_SELECTOR)
        if not element:
            return None

        text = await element.inner_text()
        return self._parse_price(text)

    async def _fetch_via_form(self, page: Page, outbound: str, return_date: str) -> Optional[float]:
        await page.goto("https://www.airfrance.fr", wait_until="networkidle", timeout=30000)
        await self._random_delay()

        await page.fill("[name='origin'], [aria-label*='Départ'], #origin", "ORY")
        await self._random_delay()
        await page.fill("[name='destination'], [aria-label*='Destination'], #destination", "FDF")
        await self._random_delay()

        d_out = self._fmt_date(outbound)
        await page.fill("[name='departureDate'], [aria-label*='Aller'], #departureDate", d_out)

        d_ret = self._fmt_date(return_date)
        await page.fill("[name='returnDate'], [aria-label*='Retour'], #returnDate", d_ret)

        await page.click("button[type='submit'], [aria-label*='Rechercher'], .af-search-btn")
        await page.wait_for_selector(_RESULTS_SELECTOR, timeout=30000)
        await self._random_delay()

        element = await page.query_selector(_PRICE_SELECTOR)
        if not element:
            return None

        text = await element.inner_text()
        return self._parse_price(text)
