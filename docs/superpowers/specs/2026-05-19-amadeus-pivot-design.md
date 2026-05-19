# Martinique Tracker — Pivot Google Flights (interception réseau)

**Date:** 2026-05-19
**Contexte:** Les 3 scrapers Playwright sont cassés (Air Caraïbes : cert SSL expiré, Corsair : sélecteurs invalides, Air France : HTTP2 block). Amadeus ne prend plus de nouveaux comptes. On pivote vers l'interception réseau de Google Flights via Playwright.

---

## Objectif

Remplacer les 3 scrapers Playwright par un unique `GoogleFlightsScraper` qui :
1. Navigue vers Google Flights avec l'URL de recherche directe ORY→FDF
2. Intercepte les réponses réseau JSON pour extraire les prix structurés
3. Filtre les résultats pour Air France (AF), Air Caraïbes (TX/Air Caraïbes) et Corsair
4. Retourne le prix minimum par compagnie

Zéro inscription, zéro quota, zéro dépendance externe supplémentaire.

---

## Changements

### Fichiers supprimés
- `scrapers/air_caraibes.py`
- `scrapers/corsair.py`
- `scrapers/air_france.py`
- `scrapers/base.py`
- `scrapers/__init__.py`
- `tests/test_scrapers.py` — remplacé

### Nouveaux fichiers
- `scrapers/google_flights.py` — scraper unique Google Flights
- `tests/test_google_flights.py` — tests unitaires avec mocks Playwright

### Fichiers modifiés
- `requirements.txt` — retire `playwright-stealth` (inutile sur Google) ; `playwright` reste
- `main.py` — remplace la boucle multi-scrapers par un appel unique par combo de dates
- `.github/workflows/check_prices.yml` — nouveau cron (5 plages horaires)

### Fichiers inchangés
- `core/price_store.py`
- `core/alert_engine.py`
- `core/notifier.py`
- `dashboard/generator.py`
- `config.py`

---

## Architecture : `scrapers/google_flights.py`

```
GoogleFlightsScraper
  get_prices(page, outbound, return_date) → dict[str, float]
    1. Enregistre un handler page.on("response", _capture)
    2. Navigue vers l'URL Google Flights :
       https://www.google.com/travel/flights?hl=fr&gl=fr
       + paramètres : ORY→FDF, dates outbound/return, 1 adulte, aller-retour
    3. Attend networkidle ou timeout 45s
    4. Parse les réponses interceptées pour extraire les prix JSON
    5. Fallback DOM : si interception vide, lit les éléments de prix dans la page
    6. Retourne {"Air France": 520.0, "Air Caraïbes": 487.0, "Corsair": 399.0}
    (compagnies absentes des résultats → absentes du dict, sans erreur)
```

**Stratégie d'interception :**
- Écoute toutes les réponses avec `page.on("response", handler)`
- Filtre les URLs contenant des patterns connus de l'API interne Google Flights
- Si le JSON contient des données de prix structurées, les parse directement
- Fallback DOM si aucune réponse utile interceptée dans les 45s

**Mapping noms compagnies :**
Google Flights affiche les noms en toutes lettres. On normalise :
- Contient "Air France" → `"Air France"`
- Contient "Air Caraïbes" ou "Air Cara" → `"Air Caraïbes"`
- Contient "Corsair" → `"Corsair"`

**Gestion d'erreur :**
- Timeout ou erreur réseau → retourne `{}`, log l'erreur
- Compagnie non trouvée dans les résultats → absente du dict (pas d'erreur)
- Le run continue dans tous les cas

---

## Flow `main.py` mis à jour

```python
scraper = GoogleFlightsScraper()

async with async_playwright() as pw:
    browser = await pw.chromium.launch(headless=True)
    context = await browser.new_context(user_agent=UA)
    page = await context.new_page()

    for route in ROUTES:
        prices = await scraper.get_prices(page, route["outbound"], route["return"])
        for airline, price in prices.items():
            records = load_prices()
            alert = detect_alert(records, airline, route["outbound"], route["return"], price)
            if alert:
                all_alerts.append(alert)
            append_price(airline, route["outbound"], route["return"], price)

    await context.close()
    await browser.close()

write_dashboard(load_prices())
if all_alerts:
    send_alert_email(all_alerts, load_prices())
```

Un seul contexte Playwright, une seule page, 4 appels séquentiels (un par combo de dates).

---

## Cron GitHub Actions

```yaml
schedule:
  - cron: '0 6,10,13,16,19 * * *'
```
= 8h, 12h, 15h, 18h, 21h heure de Paris (UTC+2 en été).

Étapes Playwright **conservées** (on garde Chromium). Étapes supprimées :
- `playwright-stealth` (plus dans requirements)

---

## Tests : `tests/test_google_flights.py`

- Parse correct d'une réponse JSON interceptée valide → retourne dict avec 3 compagnies
- Normalisation des noms de compagnies (casse, variantes)
- Prix minimum retenu quand plusieurs offres par compagnie
- Retour `{}` si réponse vide
- Retour `{}` si exception réseau
- Fallback DOM appelé si interception ne retourne rien

---

## Inscription / prérequis

Aucun. Playwright est déjà installé et fonctionnel dans le workflow.
