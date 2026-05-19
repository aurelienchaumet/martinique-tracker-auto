import asyncio
import re
from datetime import datetime
from typing import Optional

from playwright.async_api import async_playwright, Page

_RESULTS_SELECTOR = "li.pIav2d, li[data-gs]"
_EXTRACT_JS = r"""
() => {
    const results = [];
    const cards = document.querySelectorAll('li.pIav2d, li[data-gs]');
    cards.forEach(card => {
        const airlineEl = card.querySelector('.sSHqwe, .h1fkLb, .Ir0Voe');
        const priceEl   = card.querySelector('.YMlIz, .FpEdX, .nA3Fge, .U3gSDe');
        if (airlineEl && priceEl) {
            results.push({
                airline: airlineEl.innerText.trim(),
                price:   priceEl.innerText.trim()
            });
        }
    });
    // Fallback : chercher tout li contenant un prix et une compagnie connue
    if (results.length === 0) {
        document.querySelectorAll('li').forEach(card => {
            const text = card.innerText;
            if (!text.includes('€')) return;
            const priceMatch = text.match(/(\d[\d  ]+)\s*€/);
            const known = ['Air France', 'Air Caraïbes', 'Air caraïbes', 'Corsair'];
            const foundAirline = known.find(a => text.toLowerCase().includes(a.toLowerCase()));
            if (priceMatch && foundAirline) {
                results.push({ airline: foundAirline, price: priceMatch[1].trim() + ' €' });
            }
        });
    }
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
        try:
            await page.goto(
                "https://www.google.com/travel/flights",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[GoogleFlights] Erreur chargement page: {e}")
            return {}

        try:
            await _fill_form(page, outbound, return_date)
        except Exception as e:
            print(f"[GoogleFlights] Erreur formulaire {outbound}→{return_date}: {e}")
            await page.screenshot(path=f"debug_form_{outbound}.png")
            return {}

        try:
            await page.wait_for_selector(_RESULTS_SELECTOR, timeout=40000)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"[GoogleFlights] Timeout résultats {outbound}→{return_date}: {e}")
            await page.screenshot(path=f"debug_results_{outbound}.png")
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


async def _fill_form(page: Page, outbound: str, return_date: str) -> None:
    # --- Origine : effacer "La Rochelle" et taper "Paris-Orly" ---
    origin = page.locator('input[aria-label="De"]').first
    await origin.click()
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await page.keyboard.type("Paris-Orly", delay=100)
    await page.wait_for_selector('[role="option"]', timeout=8000)
    options = page.locator('[role="option"]')
    ory = options.filter(has_text="ORY")
    if await ory.count() > 0:
        await ory.first.click()
    else:
        await options.first.click()
    await page.wait_for_timeout(500)

    # --- Destination ---
    dest = page.locator('input[aria-label="À "]').first
    await dest.click()
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await page.keyboard.type("Fort-de-France", delay=100)
    await page.wait_for_selector('[role="option"]', timeout=8000)
    options = page.locator('[role="option"]')
    fdf = options.filter(has_text="FDF")
    if await fdf.count() > 0:
        await fdf.first.click()
    else:
        await options.first.click()
    await page.wait_for_timeout(500)

    # --- Date aller ---
    outbound_fr = _fmt(outbound)
    depart = page.locator('input[aria-label="Départ"]').first
    await depart.click()
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await page.keyboard.type(outbound_fr, delay=80)
    await page.wait_for_timeout(400)

    # --- Date retour ---
    return_fr = _fmt(return_date)
    retour = page.locator('input[aria-label="Retour"]').first
    await retour.click()
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await page.keyboard.type(return_fr, delay=80)
    await page.wait_for_timeout(400)

    # --- Fermer le calendrier puis lancer la recherche ---
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)
    await page.locator('button[aria-label="Rechercher des destinations"]').click()


def _fmt(date_iso: str) -> str:
    """2026-12-28 → 28/12/2026"""
    dt = datetime.strptime(date_iso, "%Y-%m-%d")
    return dt.strftime("%d/%m/%Y")


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
