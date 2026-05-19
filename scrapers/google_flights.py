import re
from typing import Optional

from playwright.async_api import Page

# Sélecteurs Google Flights (à mettre à jour si Google change son UI)
# Plusieurs variantes pour couvrir différentes versions de l'interface
_RESULTS_SELECTOR = "li.pIav2d, li[data-gs], ul[role='list'] li, [data-result-index]"
_EXTRACT_JS = """
() => {
    const results = [];
    // Essai 1 : sélecteurs classiques
    let cards = document.querySelectorAll('li.pIav2d, li[data-gs]');
    if (cards.length === 0) {
        // Essai 2 : éléments de liste avec rôle
        cards = document.querySelectorAll('[role="listitem"]');
    }
    cards.forEach(card => {
        const airlineEl = card.querySelector('.sSHqwe, .h1fkLb, .Ir0Voe, [data-airline], .operator');
        const priceEl   = card.querySelector('.YMlIz, .FpEdX, .nA3Fge, [data-price], .price');
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

# JS de diagnostic pour comprendre la structure DOM réelle
_DIAG_JS = """
() => {
    const liCount    = document.querySelectorAll('li').length;
    const pIav2d     = document.querySelectorAll('li.pIav2d').length;
    const dataGs     = document.querySelectorAll('li[data-gs]').length;
    const listitem   = document.querySelectorAll('[role="listitem"]').length;
    const bodyText   = document.body.innerText.slice(0, 300);
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
        url = _build_search_url(outbound, return_date)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            # Attendre que les résultats apparaissent (jusqu'à 60s)
            await page.wait_for_selector(_RESULTS_SELECTOR, timeout=60000)
            await page.wait_for_timeout(2000)
        except Exception as e:
            title = await page.title()
            final_url = page.url
            print(f"[GoogleFlights] Erreur chargement {outbound}→{return_date}: {e}")
            print(f"[GoogleFlights] Page title: {title!r} | URL: {final_url[:120]}")
            # Diagnostic DOM pour comprendre ce que la page contient
            try:
                diag = await page.evaluate(_DIAG_JS)
                print(f"[GoogleFlights] DOM diag: li={diag['liCount']} pIav2d={diag['pIav2d']} "
                      f"data-gs={diag['dataGs']} listitem={diag['listitem']}")
                print(f"[GoogleFlights] Body preview: {diag['bodyText'][:200]!r}")
            except Exception:
                pass
            return {}

        try:
            cards = await page.evaluate(_EXTRACT_JS)
        except Exception as e:
            print(f"[GoogleFlights] Erreur extraction DOM: {e}")
            return {}

        if not cards:
            # Diagnostic si aucune carte trouvée malgré le sélecteur
            try:
                diag = await page.evaluate(_DIAG_JS)
                print(f"[GoogleFlights] Aucune carte extraite. DOM diag: "
                      f"li={diag['liCount']} pIav2d={diag['pIav2d']} "
                      f"data-gs={diag['dataGs']} listitem={diag['listitem']}")
            except Exception:
                pass

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
