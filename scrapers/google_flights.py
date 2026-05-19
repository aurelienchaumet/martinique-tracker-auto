import re
from typing import Optional

from playwright.async_api import Page

# Sélecteurs pour les résultats de vols
_RESULTS_SELECTOR = "li.pIav2d, li[data-gs]"

_EXTRACT_JS = """
() => {
    const results = [];
    let cards = document.querySelectorAll('li.pIav2d, li[data-gs]');
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

# JS de diagnostic DOM
_DIAG_JS = """
() => {
    const liCount    = document.querySelectorAll('li').length;
    const pIav2d     = document.querySelectorAll('li.pIav2d').length;
    const dataGs     = document.querySelectorAll('li[data-gs]').length;
    const listitem   = document.querySelectorAll('[role="listitem"]').length;
    const bodyText   = document.body.innerText.slice(0, 400);
    return { liCount, pIav2d, dataGs, listitem, bodyText };
}
"""

_AIRLINE_PATTERNS = {
    "Air France":   re.compile(r"air\s+france",       re.IGNORECASE),
    "Air Caraïbes": re.compile(r"air\s+cara[ïi]bes",  re.IGNORECASE),
    "Corsair":      re.compile(r"corsair",             re.IGNORECASE),
}


class GoogleFlightsScraper:
    name = "Google Flights"

    async def get_prices(self, page: Page, outbound: str, return_date: str) -> dict[str, float]:
        """Scrape via URL directe Google Flights avec attente réseau."""
        url = _build_search_url(outbound, return_date)
        try:
            # Charger la page et attendre que le réseau soit calme
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)

            # Log pour diagnostic
            diag = await page.evaluate(_DIAG_JS)
            print(f"[GoogleFlights] Après networkidle {outbound}→{return_date}: "
                  f"li={diag['liCount']} pIav2d={diag['pIav2d']} data-gs={diag['dataGs']}")
            print(f"[GoogleFlights] Body: {diag['bodyText'][:150]!r}")

            # Si toujours sur l'accueil (peu de li), forcer une recherche via Enter
            if diag['pIav2d'] == 0 and diag['dataGs'] == 0:
                print(f"[GoogleFlights] Pas de résultats après networkidle, tentative via formulaire...")
                # Essayer de trouver un bouton Rechercher et cliquer dessus
                for selector in [
                    "button[aria-label*='Rechercher']",
                    "button[aria-label*='Search']",
                    "[jsname='vLv7Lb']",
                    "button.MXvFbd",
                ]:
                    btn = await page.query_selector(selector)
                    if btn:
                        await btn.click()
                        print(f"[GoogleFlights] Clic bouton: {selector}")
                        await page.wait_for_timeout(5000)
                        break

                # Nouvelle tentative d'attente des résultats
                await page.wait_for_selector(_RESULTS_SELECTOR, timeout=30000)
                await page.wait_for_timeout(2000)

        except Exception as e:
            title = await page.title()
            final_url = page.url
            print(f"[GoogleFlights] Erreur chargement {outbound}→{return_date}: {e}")
            print(f"[GoogleFlights] Page title: {title!r} | URL: {final_url[:120]}")
            try:
                diag = await page.evaluate(_DIAG_JS)
                print(f"[GoogleFlights] DOM diag: li={diag['liCount']} pIav2d={diag['pIav2d']} "
                      f"data-gs={diag['dataGs']} listitem={diag['listitem']}")
                print(f"[GoogleFlights] Body: {diag['bodyText'][:200]!r}")
            except Exception:
                pass
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

        return prices


def _build_search_url(outbound: str, return_date: str) -> str:
    # URL hash format Google Flights : aller-retour avec dates directes
    return (
        "https://www.google.com/travel/flights"
        f"#flt=ORY.FDF.{outbound}*FDF.ORY.{return_date}"
        ";c:EUR;e:1;sd:1;t:f"
    )


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
