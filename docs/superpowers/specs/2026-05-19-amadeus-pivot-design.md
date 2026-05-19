# Martinique Tracker — Pivot Amadeus API

**Date:** 2026-05-19
**Contexte:** Les 3 scrapers Playwright sont cassés (Air Caraïbes : cert SSL expiré, Corsair : sélecteurs invalides, Air France : HTTP2 block). On pivote vers l'API officielle Amadeus for Developers.

---

## Objectif

Remplacer les scrapers Playwright par un client Amadeus qui récupère les prix ORY→FDF pour Air France (AF), Air Caraïbes (TX) et Corsair (SS), sur 4 combinaisons de dates déc 2026/jan 2027, 5 fois par jour.

---

## Changements

### Fichiers supprimés / retirés
- `scrapers/air_caraibes.py` — supprimé
- `scrapers/corsair.py` — supprimé
- `scrapers/air_france.py` — supprimé
- `scrapers/base.py` — supprimé
- `scrapers/__init__.py` — supprimé

### Nouveaux fichiers
- `core/amadeus_client.py` — client Amadeus : auth OAuth2 + appel Flight Offers Search

### Fichiers modifiés
- `requirements.txt` — retire playwright, playwright-stealth ; ajoute `amadeus`
- `config.py` — ajoute `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET`
- `main.py` — remplace la boucle scrapers par le client Amadeus
- `.github/workflows/check_prices.yml` — nouveau cron + suppression des étapes Playwright

### Fichiers inchangés
- `core/price_store.py`
- `core/alert_engine.py`
- `core/notifier.py`
- `dashboard/generator.py`

---

## Architecture : `core/amadeus_client.py`

```
AmadeusClient
  __init__(client_id, client_secret)
  _authenticate() → bearer token (cache 29 min)
  get_prices(outbound, return_date) → dict[airline_name, float]
    GET /v2/shopping/flight-offers
      originLocationCode=ORY
      destinationLocationCode=FDF
      departureDate=outbound
      returnDate=return_date
      adults=1
      currencyCode=EUR
      max=50
    → filtrer itinéraires dont carrierCode in {AF, TX, SS}
    → prendre le prix minimum par compagnie
    → retourner {"Air France": 520.0, "Air Caraïbes": 487.0, ...}
```

**Mapping IATA → nom affiché :**
- `AF` → `Air France`
- `TX` → `Air Caraïbes`
- `SS` → `Corsair`

**Gestion d'erreur :** si l'appel échoue (timeout, quota, 4xx/5xx), `get_prices()` retourne `{}` et log l'erreur. Le run continue sans crasher.

---

## Flow `main.py` mis à jour

```python
client = AmadeusClient(AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET)
for route in ROUTES:
    prices = client.get_prices(route["outbound"], route["return"])
    for airline, price in prices.items():
        records = load_prices()
        alert = detect_alert(records, airline, route["outbound"], route["return"], price)
        if alert:
            all_alerts.append(alert)
        append_price(airline, route["outbound"], route["return"], price)
write_dashboard(load_prices())
if all_alerts:
    send_alert_email(all_alerts, load_prices())
```

Pas de Playwright, pas de navigateur, pas d'async requis.

---

## Cron GitHub Actions

```yaml
schedule:
  - cron: '0 6,10,13,16,19 * * *'
```
= 8h, 12h, 15h, 18h, 21h heure de Paris (UTC+2 en été).

**Étapes Playwright supprimées :**
- Install Chromium system dependencies
- Cache Playwright browsers
- Install Playwright Chromium browser

**Nouvelle étape :** `pip install -r requirements.txt` suffit (pas de binaires).

---

## GitHub Secrets à ajouter

| Secret | Valeur |
|--------|--------|
| `AMADEUS_CLIENT_ID` | Client ID depuis developers.amadeus.com |
| `AMADEUS_CLIENT_SECRET` | Client Secret depuis developers.amadeus.com |

Les secrets existants (`GMAIL_USER`, `GMAIL_APP_PASSWORD`, `RECIPIENT_EMAIL`) restent inchangés.

---

## Volume d'appels API

- 4 combos de dates × 5 runs/jour = **20 appels/jour**
- ~600 appels/mois
- Quota Amadeus free (production) : largement suffisant

---

## Tests

- `tests/test_amadeus_client.py` — mock `requests.post` (auth) et `requests.get` (search) :
  - parsing correct d'une réponse Amadeus valide
  - filtrage des compagnies hors périmètre (AF/TX/SS uniquement)
  - prix minimum retenu quand plusieurs offres par compagnie
  - retour `{}` si réponse vide ou erreur réseau
  - cache du token (pas de double auth sur appels successifs)
- `tests/test_scrapers.py` — supprimé (plus de scrapers)

---

## Inscription Amadeus

1. Créer un compte sur [developers.amadeus.com](https://developers.amadeus.com)
2. Créer une app → récupérer `Client ID` et `Client Secret`
3. Passer l'app en mode **Production** (formulaire simple, validation quasi-immédiate)
4. Ajouter les deux secrets dans GitHub → Settings → Secrets → Actions
