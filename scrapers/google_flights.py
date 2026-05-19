import asyncio
import re
from datetime import datetime
from typing import Optional

from playwright.async_api import async_playwright, Page

_RESULTS_SELECTOR = "div.CylAxb[data-gs]"
_EXTRACT_JS = r"""
() => {
    const results = [];
    const seen = new Set();

    // div.CylAxb[data-gs] = prix de vol (spécifique aux résultats, pas au calendrier)
    document.querySelectorAll('div.CylAxb[data-gs]').forEach(priceEl => {
        const price = priceEl.innerText.trim();
        if (!price.includes('€')) return;

        // Remonter jusqu'à la carte de vol (div.yg1Os)
        const card = priceEl.closest('.yg1Os')
                  || priceEl.parentElement?.parentElement?.parentElement;
        if (!card) return;

        const cardText = card.innerText.trim();
        const key = cardText.slice(0, 40);
        if (seen.has(key)) return;
        seen.add(key);

        results.push({ airline: cardText, price: price });
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
        try:
            await page.goto(
                "https://www.google.com/travel/flights",
                wait_until="domcontentloaded",
                timeout=45000,
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

        # Attendre la navigation vers la page résultats avec les dates
        try:
            await page.wait_for_url(
                lambda url: "travel/flights" in url and "tfs=" in url,
                timeout=20000,
            )
        except Exception as e:
            print(f"[GoogleFlights] Pas de navigation résultats {outbound}→{return_date}: {page.url}")
            await page.screenshot(path=f"debug_url_{outbound}.png")
            return {}

        print(f"[GoogleFlights] URL finale : {page.url[:120]}")

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
            print(f"[GoogleFlights] {card['airline'][:60]!r} → {airline} {price:.0f}€")

        return prices


async def _fill_form(page: Page, outbound: str, return_date: str) -> None:
    # --- Origine ---
    origin = page.locator('input[aria-label="De"]').first
    await origin.click()
    await page.wait_for_timeout(1000)
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await page.wait_for_timeout(500)
    await page.keyboard.type("Paris-Orly", delay=100)
    await page.wait_for_timeout(2000)
    ory = page.locator('[role="option"]', has_text="ORY")
    await ory.first.wait_for(state="visible", timeout=8000)
    await ory.first.click()
    await page.wait_for_timeout(500)

    # --- Destination ---
    # Après FDF, la page auto-navigue vers travel/flights?tfs=... (ORY+FDF, sans dates)
    dest = page.locator('input[aria-label="À "]').first
    await dest.click()
    await page.wait_for_timeout(1000)
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await page.wait_for_timeout(500)
    await page.keyboard.type("Fort-de-France", delay=100)
    await page.wait_for_timeout(2000)
    fdf = page.locator('[role="option"]', has_text="FDF")
    await fdf.first.wait_for(state="visible", timeout=8000)
    await fdf.first.click()

    # Attendre l'auto-navigation vers la page résultats ORY+FDF
    await page.wait_for_url(
        lambda url: "travel/flights" in url and "tfs=" in url,
        timeout=12000,
    )
    await page.wait_for_timeout(2000)

    # --- Mettre à jour les dates sur la page de résultats (contexte ORY+FDF correct) ---
    outbound_fr = _fmt(outbound)
    return_fr = _fmt(return_date)
    dialog_selector = '[role="dialog"][aria-modal="true"]:has(input[aria-label="Départ"])'

    # Clic sur Départ pour ouvrir le calendrier (maintenant en contexte ORY+FDF)
    await page.locator('input[aria-label="Départ"]').first.click()
    await page.wait_for_timeout(800)
    await page.wait_for_selector(dialog_selector, timeout=8000)

    # Saisir date aller dans le dialog
    dialog_depart = page.locator(f'{dialog_selector} input[aria-label="Départ"]')
    await dialog_depart.click()
    await page.wait_for_timeout(300)
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await page.keyboard.type(outbound_fr, delay=80)
    await page.wait_for_timeout(600)

    # Saisir date retour
    await page.keyboard.press("Tab")
    await page.wait_for_timeout(300)
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await page.keyboard.type(return_fr, delay=80)
    await page.wait_for_timeout(400)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(600)

    # Clic JS sur OK pour valider les dates
    await page.evaluate("document.querySelector('button[jsname=\"McfNlf\"]').click()")
    await page.wait_for_timeout(1000)

    # Cliquer le bouton Rechercher du formulaire principal pour soumettre
    search_btn = page.locator('button[jsname="vLv7Lb"], button[aria-label="Rechercher"]').first
    if await search_btn.count() == 0:
        # Fallback : chercher par texte en excluant les liens du bas de page
        search_btn = page.get_by_role("button", name="Rechercher")
    await search_btn.first.click()
    await page.wait_for_timeout(2000)


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
