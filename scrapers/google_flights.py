import asyncio
import re
from typing import Optional

from playwright.async_api import async_playwright, Page

_RESULTS_SELECTOR = "li.pIav2d, li[data-gs]"
_EXTRACT_JS = """
() => {
    const results = [];
    const cards = document.querySelectorAll('li.pIav2d, li[data-gs]');
    cards.forEach(card => {
        const airlineEl = card.querySelector('.sSHqwe, .h1fkLb, .Ir0Voe');
        const priceEl   = card.querySelector('.YMlIz, .FpEdX, .nA3Fge');
        if (airlineEl && priceEl) {
            results.push({
                airline: airlineEl.innerText.trim(),
                price:   priceEl.innerText.trim()
            });
        }
    });
    return results;
}
"""

_AIRLINE_PATTERNS = {
    "Air France":   re.compile(r"air\s+france",      re.IGNORECASE),
    "Air Caraïbes": re.compile(r"air\s+cara[ïi]bes", re.IGNORECASE),
    "Corsair":      re.compile(r"corsair",            re.IGNORECASE),
}


class GoogleFlightsScraper:
    name = "Google Flights"

    async def get_prices(self, page: Page, outbound: str, return_date: str) -> dict[str, float]:
        url = (
            "https://www.google.com/travel/flights"
            f"#flt=ORY.FDF.{outbound}*FDF.ORY.{return_date}"
            ";c:EUR;e:1;sd:1;t:f"
        )
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)

            # Gérer la page de consentement Google (consent.google.com)
            if "consent.google.com" in page.url:
                await page.click(
                    "button:has-text('Tout accepter'), button:has-text('Accept all')",
                    timeout=10000
                )
                await page.wait_for_url("**/travel/flights**", timeout=15000)
                await page.wait_for_load_state("domcontentloaded")

            await page.wait_for_selector(_RESULTS_SELECTOR, timeout=30000)
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[GoogleFlights] Erreur chargement {outbound}→{return_date}: {e}")
            return {}

        try:
            cards = await page.evaluate(_EXTRACT_JS)
        except Exception as e:
            print(f"[GoogleFlights] Erreur extraction DOM: {e}")
            return {}

        prices: dict[str, float] = {}
        for card in (cards or []):
            airline = _normalize_airline(card.get("airline", ""))
            price   = _parse_price(card.get("price", ""))
            if airline is None or price is None:
                continue
            if airline not in prices or price < prices[airline]:
                prices[airline] = price
            print(f"[GoogleFlights] {card['airline']!r} {card['price']!r} → {airline} {price:.0f}€")

        return prices


def _normalize_airline(text: str) -> Optional[str]:
    for name, pattern in _AIRLINE_PATTERNS.items():
        if pattern.search(text):
            return name
    return None


def _parse_price(text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d\s,.]", "", text).strip()
    cleaned = re.sub(r"(\d)\s(\d)", r"\1\2", cleaned)
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None
