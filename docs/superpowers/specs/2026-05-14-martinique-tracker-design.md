# Design — Martinique Flight Price Tracker

**Date:** 2026-05-14  
**Statut:** Approuvé

---

## Contexte

Outil de surveillance des prix de vols Paris Orly (ORY) → Martinique (MQM/FDF) pour une période de départ/retour fixe avec flexibilité de ±1 jour. L'outil détecte les chutes et hausses de prix en temps réel et notifie l'utilisateur.

---

## Combinaisons surveillées

| # | Aller | Retour |
|---|-------|--------|
| 1 | 28 décembre 2026 | 15 janvier 2027 |
| 2 | 28 décembre 2026 | 16 janvier 2027 |
| 3 | 29 décembre 2026 | 15 janvier 2027 |
| 4 | 29 décembre 2026 | 16 janvier 2027 |

**Compagnies surveillées :** Air France, Air Caraïbes, Corsair

---

## Architecture

```
GitHub Actions (cron toutes les heures)
        │
        ▼
   main.py
   ├── Scrapers (Playwright + playwright-stealth)
   │   ├── Air France
   │   ├── Air Caraïbes
   │   └── Corsair
   │
   ├── Price Store → data/prices.json (versionné dans git)
   │
   ├── Alert Engine
   │   └── Variation > 20€ → déclenche Notifier
   │
   ├── Notifier
   │   ├── Email HTML (Gmail SMTP)
   │   └── Snapshot PDF en pièce jointe (matplotlib)
   │
   └── Dashboard Generator
       └── index.html (Chart.js) → déployé sur Netlify
```

---

## Structure des fichiers

```
martinique-tracker/
├── .github/
│   └── workflows/
│       └── check_prices.yml
├── scrapers/
│   ├── base.py
│   ├── air_france.py
│   ├── air_caraibes.py
│   └── corsair.py
├── core/
│   ├── price_store.py
│   ├── alert_engine.py
│   └── notifier.py
├── dashboard/
│   └── generator.py
├── data/
│   └── prices.json
├── config.py
└── main.py
```

---

## Format des données (prices.json)

```json
[
  {
    "timestamp": "2026-10-01T08:00:00",
    "airline": "Air Caraïbes",
    "outbound": "2026-12-28",
    "return": "2027-01-15",
    "price": 487.00,
    "currency": "EUR"
  }
]
```

---

## Scraping

- **Outil :** Playwright (Chromium headless) + `playwright-stealth`
- **Stratégie :** Délais aléatoires 2–5s entre requêtes, rotation user-agent
- **Résilience :** Échec silencieux si timeout ou blocage — pas d'alerte parasite
- **Caching GitHub Actions :** Installation Playwright mise en cache pour rester sous 2 000 min/mois (free plan repo privé)

---

## Logique d'alerte

- Comparaison du nouveau prix avec le dernier prix enregistré (par compagnie + combinaison)
- Seuil : `|nouveau - ancien| > 20€`
- Types : **CHUTE** (↓) ou **HAUSSE** (↑)
- Premier enregistrement d'une combinaison → baseline, pas d'alerte

**Email d'alerte :**
- Objet : `✈️ [CHUTE -45€] Air Caraïbes 28/12 → 15/01`
- Corps HTML : tableau des 4 combinaisons (prix actuel, ancien prix, variation)
- Pièce jointe : snapshot PDF des graphiques

**Credentials (GitHub Secrets) :**
- `GMAIL_USER`
- `GMAIL_APP_PASSWORD`
- `RECIPIENT_EMAIL`

---

## Dashboard (Netlify)

- Généré à chaque check, poussé automatiquement via GitHub → Netlify
- **4 graphiques de courbes** (Chart.js) — un par combinaison, une couleur par compagnie
- **Tableau récapitulatif :** prix actuel, min historique, max historique, dernière variation
- **Indicateur visuel :** vert si proche du min, rouge si proche du max
- Dernière mise à jour affichée en haut de page

**PDF snapshot (email) :**
- Généré avec `matplotlib`
- Contient les 4 graphiques + tableau récapitulatif
- Nom : `martinique_prix_YYYY-MM-DD_HH.pdf`

---

## GitHub Actions

```yaml
on:
  schedule:
    - cron: '0 * * * *'   # toutes les heures
  workflow_dispatch:        # déclenchement manuel possible

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - Checkout
      - Setup Python + cache Playwright
      - Install dépendances
      - Run main.py
      - Commit prices.json + index.html si changement
```

---

## Hébergement

| Composant | Service | Coût |
|-----------|---------|------|
| Scheduler + code | GitHub (repo privé) | Gratuit (2 000 min/mois) |
| Dashboard | Netlify | Gratuit |
| Emails | Gmail SMTP | Gratuit |

---

## Hors scope

- Comparaison avec d'autres destinations
- Réservation automatique
- Application mobile native
- Support d'autres aéroports de départ
