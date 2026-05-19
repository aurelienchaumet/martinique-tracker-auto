# Pivot Google Flights — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer les 3 scrapers Playwright cassés par un unique `GoogleFlightsScraper` qui extrait les prix ORY→FDF depuis le DOM de Google Flights.

**Architecture:** Un seul scraper `scrapers/google_flights.py` navigue vers Google Flights via une URL encodée contenant les dates, attend le rendu des cartes de vol, et extrait les prix via `page.evaluate()`. `main.py` est simplifié : une boucle sur 4 combos de dates, un appel scraper par combo. Le cron passe à 5 plages horaires (8h/12h/15h/18h/21h Paris). Le reste de la stack (price_store, alert_engine, notifier, dashboard) est inchangé.

**Tech Stack:** Python 3.11, Playwright 1.49.1, pytest, pytest-asyncio, GitHub Actions

---

## File Map

| Fichier | Action | Responsabilité |
|---------|--------|----------------|
| `scrapers/google_flights.py` | Créer | Scraper unique Google Flights |
| `scrapers/__init__.py` | Recréer vide | Package marker |
| `tests/test_google_flights.py` | Créer | Tests unitaires avec mocks Playwright |
| `scrapers/air_caraibes.py` | Supprimer | Remplacé |
| `scrapers/air_france.py` | Supprimer | Remplacé |
| `scrapers/corsair.py` | Supprimer | Remplacé |
| `scrapers/base.py` | Supprimer | Remplacé |
| `tests/test_scrapers.py` | Supprimer | Remplacé par test_google_flights.py |
| `requirements.txt` | Modifier | Retirer playwright-stealth |
| `main.py` | Modifier | Remplacer boucle multi-scrapers |
| `.github/workflows/check_prices.yml` | Modifier | Nouveau cron, retirer étapes stealth |

---

## Task 1: Nettoyage des anciens scrapers

**Files:**
- Delete: `scrapers/air_caraibes.py`, `scrapers/corsair.py`, `scrapers/air_france.py`, `scrapers/base.py`, `scrapers/__init__.py`
- Delete: `tests/test_scrapers.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Supprimer les anciens scrapers et leurs tests**

```bash
git rm scrapers/air_caraibes.py scrapers/corsair.py scrapers/air_france.py scrapers/base.py scrapers/__init__.py
git rm tests/test_scrapers.py
```

Expected : 5+1 fichiers supprimés du staging.

- [ ] **Step 2: Mettre à jour `requirements.txt`**

Remplacer le contenu complet par :

```
playwright==1.49.1
matplotlib==3.8.4
pytest==8.2.0
pytest-asyncio==0.23.6
```

(`playwright-stealth` retiré — inutile sur Google.)

- [ ] **Step 3: Vérifier que les tests existants passent toujours**

```bash
pytest tests/test_price_store.py tests/test_alert_engine.py tests/test_notifier.py tests/test_dashboard_generator.py -v
```

Expected : tous PASSED. Si erreur d'import sur les anciens scrapers, vérifier que `main.py` n'a pas encore été mis à jour (c'est normal, on le fera en Task 3).

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: supprimer anciens scrapers et playwright-stealth"
```

---

## Task 2: GoogleFlightsScraper — TDD

**Files:**
- Create: `scrapers/__init__.py`
- Create: `scrapers/google_flights.py`
- Create: `tests/test_google_flights.py`

- [ ] **Step 1: Recréer `scrapers/__init__.py` vide**

Sur Windows PowerShell :
```powershell
New-Item scrapers/__init__.py -ItemType File
```

- [ ] **Step 2: Écrire les tests**

Créer `tests/test_google_flights.py` :

```python
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
```

- [ ] **Step 3: Lancer les tests pour vérifier qu'ils échouent**

```bash
pytest tests/test_google_flights.py -v
```

Expected : `ModuleNotFoundError: No module named 'scrapers.google_flights'`

- [ ] **Step 4: Implémenter `scrapers/google_flights.py`**

```python
import re
from typing import Optional

from playwright.async_api import Page

# Sélecteurs Google Flights (à mettre à jour si Google change son UI)
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
    "Air France":   re.compile(r"air\s+france",       re.IGNORECASE),
    "Air Caraïbes": re.compile(r"air\s+cara[ïi]bes",  re.IGNORECASE),
    "Corsair":      re.compile(r"corsair",             re.IGNORECASE),
}


class GoogleFlightsScraper:
    name = "Google Flights"

    async def get_prices(self, page: Page, outbound: str, return_date: str) -> dict[str, float]:
        url = _build_search_url(outbound, return_date)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
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
```

- [ ] **Step 5: Lancer les tests pour vérifier qu'ils passent**

```bash
pytest tests/test_google_flights.py -v
```

Expected : 15 tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add scrapers/ tests/test_google_flights.py
git commit -m "feat: GoogleFlightsScraper extraction DOM Google Flights"
```

---

## Task 3: Mettre à jour `main.py`

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Remplacer le contenu de `main.py`**

```python
import asyncio
from typing import List

from playwright.async_api import async_playwright

from config import ROUTES
from core.alert_engine import Alert, detect_alert
from core.notifier import send_alert_email
from core.price_store import append_price, load_prices
from dashboard.generator import write_dashboard
from scrapers.google_flights import GoogleFlightsScraper

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)


async def run():
    scraper = GoogleFlightsScraper()
    all_alerts: List[Alert] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=UA)
        page = await context.new_page()

        for route in ROUTES:
            outbound = route["outbound"]
            ret = route["return"]

            prices = await scraper.get_prices(page, outbound, ret)
            if not prices:
                print(f"[main] Aucun prix pour {outbound}→{ret}")
                continue

            for airline, price in prices.items():
                print(f"[main] {airline} {outbound}→{ret}: {price:.0f}€")
                records = load_prices()
                alert = detect_alert(records, airline, outbound, ret, price)
                if alert:
                    print(f"[main] ALERTE: {alert.airline} {alert.label}")
                    all_alerts.append(alert)
                append_price(airline, outbound, ret, price)

        await context.close()
        await browser.close()

    records = load_prices()
    write_dashboard(records)

    if all_alerts:
        send_alert_email(all_alerts, records)
    else:
        print("[main] Aucune alerte — prix stables.")


if __name__ == "__main__":
    asyncio.run(run())
```

- [ ] **Step 2: Vérifier que les imports fonctionnent**

```bash
python -c "from main import run; print('main.py OK')"
```

Expected : `main.py OK`

- [ ] **Step 3: Lancer la suite de tests complète**

```bash
pytest tests/ -v --tb=short
```

Expected : tous les tests PASSED (test_google_flights + les 4 anciens modules).

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: main.py pivote sur GoogleFlightsScraper"
```

---

## Task 4: Mettre à jour le workflow GitHub Actions

**Files:**
- Modify: `.github/workflows/check_prices.yml`

- [ ] **Step 1: Remplacer le contenu du workflow**

```yaml
name: Check Flight Prices

on:
  schedule:
    - cron: '0 6,10,13,16,19 * * *'
  workflow_dispatch:

concurrency:
  group: price-check
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  check:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: pip

      - name: Install Python dependencies
        run: pip install -r requirements.txt

      - name: Install Chromium system dependencies (Ubuntu 24.04)
        run: |
          sudo apt-get install -y --no-install-recommends \
            libasound2t64 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 \
            libgtk-3-0t64 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 \
            libxrandr2 libgbm1 libnss3 libnspr4 libpango-1.0-0 libcairo2 \
            libx11-xcb1 libdbus-1-3 libdrm2 libglib2.0-0t64

      - name: Cache Playwright browsers
        id: playwright-cache
        uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: playwright-chromium-${{ runner.os }}-${{ hashFiles('requirements.txt') }}

      - name: Install Playwright Chromium browser
        if: steps.playwright-cache.outputs.cache-hit != 'true'
        run: playwright install chromium

      - name: Run price check
        env:
          GMAIL_USER: ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
        run: python main.py

      - name: Commit updated data and dashboard
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/prices.json dashboard/index.html
          git diff --staged --quiet || git commit -m "chore: update prices $(date -u '+%Y-%m-%d %H:%M UTC')"
          git push
```

- [ ] **Step 2: Commit et push**

```bash
git add .github/workflows/check_prices.yml
git commit -m "chore: cron 8h/12h/15h/18h/21h Paris, retirer playwright-stealth"
git push
```

---

## Task 5: Vérification live

- [ ] **Step 1: Déclencher un run manuel sur GitHub Actions**

Sur GitHub → onglet Actions → "Check Flight Prices" → bouton "Run workflow".

Surveiller les logs. Chercher :
```
[main] Air France 2026-12-28→2027-01-15: XXX€
[main] Air Caraïbes 2026-12-28→2027-01-15: XXX€
[main] Corsair 2026-12-28→2027-01-15: XXX€
```

- [ ] **Step 2: Si les logs affichent `Aucun prix` — mettre à jour les sélecteurs**

Les sélecteurs CSS de Google Flights peuvent avoir changé. Pour trouver les bons :
1. Ouvrir `https://www.google.com/travel/flights#flt=ORY.FDF.2026-12-28*FDF.ORY.2027-01-15;c:EUR;e:1;sd:1;t:f` dans Chrome
2. Ouvrir DevTools (F12) → inspecter une carte de vol
3. Identifier le sélecteur du nom de compagnie et du prix
4. Mettre à jour `_RESULTS_SELECTOR` et `_EXTRACT_JS` dans `scrapers/google_flights.py`
5. Relancer le workflow

- [ ] **Step 3: Vérifier `data/prices.json` après un run réussi**

```bash
git pull
python -c "import json; d=json.load(open('data/prices.json')); print(f'{len(d)} enregistrements'); [print(r) for r in d[-3:]]"
```

Expected : au moins 1 enregistrement avec un prix réel.

- [ ] **Step 4: Commit si ajustements de sélecteurs**

```bash
git add scrapers/google_flights.py
git commit -m "fix: sélecteurs CSS Google Flights mis à jour"
git push
```
