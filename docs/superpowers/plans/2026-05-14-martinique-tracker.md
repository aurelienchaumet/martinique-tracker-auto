# Martinique Flight Price Tracker — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python tool that scrapes flight prices (Air France, Air Caraïbes, Corsair) for 4 ORY→FDF round-trip combinations in Dec 2026/Jan 2027, detects changes > 20€, sends email alerts with PDF snapshots, and maintains a live Chart.js dashboard deployed to Netlify.

**Architecture:** GitHub Actions (hourly cron) runs `main.py`, which calls three Playwright scrapers, compares prices against a versioned `data/prices.json` history, triggers email alerts on significant changes, regenerates the static HTML dashboard, and commits all changes back to the repo (Netlify auto-deploys on push).

**Tech Stack:** Python 3.11, playwright + playwright-stealth, matplotlib, smtplib, pytest, GitHub Actions, Netlify

---

## File Map

| File | Responsibility |
|------|---------------|
| `config.py` | Route combinations, IATA codes, threshold, env var names |
| `data/prices.json` | Append-only price history (versioned in git) |
| `core/price_store.py` | Read/write/query `prices.json` |
| `core/alert_engine.py` | Detect price changes above threshold |
| `core/notifier.py` | Send HTML email + PDF attachment via Gmail SMTP |
| `scrapers/base.py` | Abstract `AirlineScraper` base class |
| `scrapers/air_caraibes.py` | Air Caraïbes Playwright scraper |
| `scrapers/corsair.py` | Corsair Playwright scraper |
| `scrapers/air_france.py` | Air France Playwright scraper |
| `dashboard/generator.py` | Generate `dashboard/index.html` with Chart.js + embedded JSON |
| `main.py` | Orchestrate all steps |
| `.github/workflows/check_prices.yml` | Hourly cron, cache Playwright, commit + push |
| `requirements.txt` | All Python dependencies |
| `tests/test_price_store.py` | Unit tests for price_store |
| `tests/test_alert_engine.py` | Unit tests for alert_engine |
| `tests/test_notifier.py` | Unit tests for notifier (mocked SMTP) |
| `tests/test_dashboard_generator.py` | Unit tests for HTML generation |
| `tests/test_scrapers.py` | Unit tests for scrapers (mocked Playwright) |

---

## Task 1: Project setup & config

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `data/.gitkeep`
- Create: `data/prices.json`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p data scrapers core dashboard tests .github/workflows
touch data/.gitkeep
```

- [ ] **Step 2: Create `requirements.txt`**

```
playwright==1.44.0
playwright-stealth==1.0.6
matplotlib==3.8.4
pytest==8.2.0
pytest-asyncio==0.23.6
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
```

Expected: no errors, Chromium downloaded.

- [ ] **Step 4: Create `config.py`**

```python
import os

ORIGIN = "ORY"
DESTINATION = "FDF"

ROUTES = [
    {"outbound": "2026-12-28", "return": "2027-01-15"},
    {"outbound": "2026-12-28", "return": "2027-01-16"},
    {"outbound": "2026-12-29", "return": "2027-01-15"},
    {"outbound": "2026-12-29", "return": "2027-01-16"},
]

ALERT_THRESHOLD = 20.0

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "")
```

- [ ] **Step 5: Create empty `data/prices.json`**

```bash
echo "[]" > data/prices.json
```

- [ ] **Step 6: Create `.gitignore`**

```
__pycache__/
*.pyc
.env
.playwright/
```

- [ ] **Step 7: Commit**

```bash
git init
git add .
git commit -m "feat: project setup and config"
```

---

## Task 2: Price store

**Files:**
- Create: `core/__init__.py`
- Create: `core/price_store.py`
- Create: `tests/__init__.py`
- Create: `tests/test_price_store.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_price_store.py`:

```python
import json
import pytest
from pathlib import Path
from core.price_store import (
    PriceRecord,
    load_prices,
    save_prices,
    append_price,
    get_last_price,
)


@pytest.fixture
def tmp_prices_path(tmp_path, monkeypatch):
    p = tmp_path / "prices.json"
    p.write_text("[]")
    monkeypatch.setattr("core.price_store.DATA_PATH", p)
    return p


def test_load_empty(tmp_prices_path):
    assert load_prices() == []


def test_save_and_load(tmp_prices_path):
    records = [
        PriceRecord(
            timestamp="2026-10-01T08:00:00",
            airline="Air Caraïbes",
            outbound="2026-12-28",
            return_date="2027-01-15",
            price=487.0,
        )
    ]
    save_prices(records)
    loaded = load_prices()
    assert len(loaded) == 1
    assert loaded[0].price == 487.0
    assert loaded[0].airline == "Air Caraïbes"


def test_append_price(tmp_prices_path):
    append_price("Corsair", "2026-12-28", "2027-01-15", 399.0)
    append_price("Corsair", "2026-12-28", "2027-01-15", 410.0)
    records = load_prices()
    assert len(records) == 2
    assert records[-1].price == 410.0


def test_get_last_price_found(tmp_prices_path):
    append_price("Air France", "2026-12-29", "2027-01-16", 520.0)
    append_price("Air France", "2026-12-29", "2027-01-16", 505.0)
    records = load_prices()
    last = get_last_price(records, "Air France", "2026-12-29", "2027-01-16")
    assert last == 505.0


def test_get_last_price_not_found(tmp_prices_path):
    records = load_prices()
    assert get_last_price(records, "Air France", "2026-12-29", "2027-01-16") is None


def test_get_last_price_ignores_other_airlines(tmp_prices_path):
    append_price("Corsair", "2026-12-28", "2027-01-15", 350.0)
    records = load_prices()
    assert get_last_price(records, "Air France", "2026-12-28", "2027-01-15") is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_price_store.py -v
```

Expected: `ModuleNotFoundError` or `ImportError` — no implementation yet.

- [ ] **Step 3: Create `core/__init__.py`**

```python
```
(empty file)

- [ ] **Step 4: Implement `core/price_store.py`**

```python
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DATA_PATH = Path(__file__).parent.parent / "data" / "prices.json"


@dataclass
class PriceRecord:
    timestamp: str
    airline: str
    outbound: str
    return_date: str
    price: float
    currency: str = "EUR"


def load_prices() -> List[PriceRecord]:
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return [PriceRecord(**r) for r in data]


def save_prices(records: List[PriceRecord]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, indent=2, ensure_ascii=False)


def append_price(airline: str, outbound: str, return_date: str, price: float) -> None:
    records = load_prices()
    records.append(
        PriceRecord(
            timestamp=datetime.now().isoformat(),
            airline=airline,
            outbound=outbound,
            return_date=return_date,
            price=price,
        )
    )
    save_prices(records)


def get_last_price(
    records: List[PriceRecord], airline: str, outbound: str, return_date: str
) -> Optional[float]:
    matches = [
        r
        for r in records
        if r.airline == airline
        and r.outbound == outbound
        and r.return_date == return_date
    ]
    return matches[-1].price if matches else None
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
pytest tests/test_price_store.py -v
```

Expected: 6 tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add core/ tests/test_price_store.py tests/__init__.py
git commit -m "feat: price store with append/load/query"
```

---

## Task 3: Alert engine

**Files:**
- Create: `core/alert_engine.py`
- Create: `tests/test_alert_engine.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_alert_engine.py`:

```python
from core.price_store import PriceRecord
from core.alert_engine import Alert, detect_alert


def _record(airline, outbound, return_date, price, ts="2026-10-01T08:00:00"):
    return PriceRecord(
        timestamp=ts,
        airline=airline,
        outbound=outbound,
        return_date=return_date,
        price=price,
    )


def test_no_alert_on_first_record():
    records = []
    alert = detect_alert(records, "Air Caraïbes", "2026-12-28", "2027-01-15", 487.0)
    assert alert is None


def test_no_alert_below_threshold():
    records = [_record("Air Caraïbes", "2026-12-28", "2027-01-15", 487.0)]
    alert = detect_alert(records, "Air Caraïbes", "2026-12-28", "2027-01-15", 500.0)
    assert alert is None


def test_alert_on_drop():
    records = [_record("Corsair", "2026-12-28", "2027-01-15", 450.0)]
    alert = detect_alert(records, "Corsair", "2026-12-28", "2027-01-15", 410.0)
    assert alert is not None
    assert alert.is_drop is True
    assert alert.delta == pytest.approx(-40.0)


def test_alert_on_rise():
    records = [_record("Air France", "2026-12-29", "2027-01-16", 500.0)]
    alert = detect_alert(records, "Air France", "2026-12-29", "2027-01-16", 530.0)
    assert alert is not None
    assert alert.is_drop is False
    assert alert.delta == pytest.approx(30.0)


def test_alert_exact_threshold_no_trigger():
    records = [_record("Corsair", "2026-12-28", "2027-01-15", 450.0)]
    alert = detect_alert(records, "Corsair", "2026-12-28", "2027-01-15", 470.0)
    assert alert is None


def test_alert_label_drop():
    records = [_record("Air Caraïbes", "2026-12-28", "2027-01-15", 487.0)]
    alert = detect_alert(records, "Air Caraïbes", "2026-12-28", "2027-01-15", 440.0)
    assert "↓" in alert.label
    assert "47" in alert.label


def test_alert_label_rise():
    records = [_record("Air Caraïbes", "2026-12-28", "2027-01-15", 440.0)]
    alert = detect_alert(records, "Air Caraïbes", "2026-12-28", "2027-01-15", 487.0)
    assert "↑" in alert.label
```

Add `import pytest` at top of test file.

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_alert_engine.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `core/alert_engine.py`**

```python
from dataclasses import dataclass
from typing import List, Optional

from config import ALERT_THRESHOLD
from core.price_store import PriceRecord, get_last_price


@dataclass
class Alert:
    airline: str
    outbound: str
    return_date: str
    old_price: float
    new_price: float

    @property
    def delta(self) -> float:
        return self.new_price - self.old_price

    @property
    def is_drop(self) -> bool:
        return self.delta < 0

    @property
    def label(self) -> str:
        sign = "↓" if self.is_drop else "↑"
        return f"{sign} {abs(self.delta):.0f}€"


def detect_alert(
    records: List[PriceRecord],
    airline: str,
    outbound: str,
    return_date: str,
    new_price: float,
    threshold: float = ALERT_THRESHOLD,
) -> Optional[Alert]:
    last = get_last_price(records, airline, outbound, return_date)
    if last is None:
        return None
    if abs(new_price - last) > threshold:
        return Alert(
            airline=airline,
            outbound=outbound,
            return_date=return_date,
            old_price=last,
            new_price=new_price,
        )
    return None
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_alert_engine.py -v
```

Expected: 7 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add core/alert_engine.py tests/test_alert_engine.py
git commit -m "feat: alert engine detects price changes above threshold"
```

---

## Task 4: Notifier (email + PDF)

**Files:**
- Create: `core/notifier.py`
- Create: `tests/test_notifier.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_notifier.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from core.alert_engine import Alert
from core.notifier import build_email_html, build_subject, generate_pdf_bytes


def _alert(airline, delta):
    old = 500.0
    new = old + delta
    return Alert(
        airline=airline,
        outbound="2026-12-28",
        return_date="2027-01-15",
        old_price=old,
        new_price=new,
    )


def test_subject_drop():
    alert = _alert("Air Caraïbes", -45.0)
    subject = build_subject(alert)
    assert "CHUTE" in subject
    assert "45" in subject
    assert "Air Caraïbes" in subject


def test_subject_rise():
    alert = _alert("Corsair", 30.0)
    subject = build_subject(alert)
    assert "HAUSSE" in subject
    assert "30" in subject


def test_email_html_contains_prices():
    alert = _alert("Air France", -25.0)
    html = build_email_html([alert])
    assert "Air France" in html
    assert "500" in html
    assert "475" in html


def test_email_html_is_valid_html():
    alert = _alert("Corsair", 22.0)
    html = build_email_html([alert])
    assert html.strip().startswith("<!DOCTYPE html")
    assert "</html>" in html


def test_generate_pdf_bytes_returns_bytes():
    from core.price_store import PriceRecord
    records = [
        PriceRecord(
            timestamp="2026-10-01T08:00:00",
            airline="Air Caraïbes",
            outbound="2026-12-28",
            return_date="2027-01-15",
            price=487.0,
        )
    ]
    pdf = generate_pdf_bytes(records)
    assert isinstance(pdf, bytes)
    assert len(pdf) > 100
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_notifier.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `core/notifier.py`**

```python
import io
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import GMAIL_APP_PASSWORD, GMAIL_USER, RECIPIENT_EMAIL, ROUTES
from core.alert_engine import Alert
from core.price_store import PriceRecord


def build_subject(alert: Alert) -> str:
    kind = "CHUTE" if alert.is_drop else "HAUSSE"
    return (
        f"✈️ [{kind} {alert.label}] {alert.airline} "
        f"{alert.outbound} → {alert.return_date}"
    )


def build_email_html(alerts: List[Alert]) -> str:
    rows = ""
    for a in alerts:
        color = "#2e7d32" if a.is_drop else "#c62828"
        rows += f"""
        <tr>
          <td>{a.airline}</td>
          <td>{a.outbound}</td>
          <td>{a.return_date}</td>
          <td>{a.old_price:.0f}€</td>
          <td style="color:{color};font-weight:bold">{a.new_price:.0f}€</td>
          <td style="color:{color}">{a.label}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:sans-serif">
  <h2>✈️ Alerte prix — Martinique</h2>
  <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse">
    <thead style="background:#1565c0;color:white">
      <tr>
        <th>Compagnie</th><th>Aller</th><th>Retour</th>
        <th>Ancien prix</th><th>Nouveau prix</th><th>Variation</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <p style="color:#888;font-size:12px">
    Mis à jour le {datetime.now().strftime("%d/%m/%Y %H:%M")}
  </p>
</body>
</html>"""


def generate_pdf_bytes(records: List[PriceRecord]) -> bytes:
    combos = [(r["outbound"], r["return"]) for r in ROUTES]
    airlines = sorted({r.airline for r in records})

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Évolution des prix ORY → FDF", fontsize=14, fontweight="bold")

    for idx, (outbound, ret) in enumerate(combos):
        ax = axes[idx // 2][idx % 2]
        ax.set_title(f"{outbound} → {ret}", fontsize=10)
        ax.set_xlabel("Date")
        ax.set_ylabel("Prix (€)")

        for airline in airlines:
            pts = [
                (r.timestamp, r.price)
                for r in records
                if r.airline == airline
                and r.outbound == outbound
                and r.return_date == ret
            ]
            if pts:
                times, prices = zip(*pts)
                ax.plot(times, prices, marker="o", label=airline, markersize=3)

        ax.legend(fontsize=8)
        ax.tick_params(axis="x", rotation=45, labelsize=7)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="pdf")
    plt.close(fig)
    return buf.getvalue()


def send_alert_email(alerts: List[Alert], records: List[PriceRecord]) -> None:
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("[notifier] No GMAIL credentials — skipping email.")
        return

    subject = build_subject(alerts[0]) if len(alerts) == 1 else "✈️ Alertes prix Martinique"
    html = build_email_html(alerts)
    pdf = generate_pdf_bytes(records)

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html, "html", "utf-8"))

    attachment = MIMEApplication(pdf, _subtype="pdf")
    filename = f"martinique_prix_{datetime.now().strftime('%Y-%m-%d_%H')}.pdf"
    attachment.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())

    print(f"[notifier] Email sent: {subject}")
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_notifier.py -v
```

Expected: 5 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add core/notifier.py tests/test_notifier.py
git commit -m "feat: email notifier with HTML body and PDF attachment"
```

---

## Task 5: Base scraper + Air Caraïbes scraper

**Files:**
- Create: `scrapers/__init__.py`
- Create: `scrapers/base.py`
- Create: `scrapers/air_caraibes.py`
- Create: `tests/test_scrapers.py`

- [ ] **Step 1: Inspect Air Caraïbes site to identify selectors**

Open `https://www.aircaribes.com` in a browser. Search for a round trip ORY → FDF. Open DevTools (F12) and identify:
- The search form URL or endpoint hit after the search
- The CSS selector for the lowest price result (typically a `<span>` or `<div>` containing the price like `487 €`)
- Note the exact selector in a comment in the scraper file

- [ ] **Step 2: Write failing scraper tests**

Create `tests/test_scrapers.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from scrapers.air_caraibes import AirCaraibesScraper
from scrapers.corsair import CorsairScraper
from scrapers.air_france import AirFranceScraper


@pytest.mark.asyncio
async def test_air_caraibes_returns_float_on_success():
    scraper = AirCaraibesScraper()
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_element = AsyncMock()
    mock_element.inner_text = AsyncMock(return_value="487 €")
    mock_page.query_selector = AsyncMock(return_value=mock_element)

    with patch.object(scraper, "_search_page", return_value=mock_page):
        price = await scraper.get_price(mock_page, "2026-12-28", "2027-01-15")

    assert isinstance(price, float)
    assert price == 487.0


@pytest.mark.asyncio
async def test_scraper_returns_none_on_timeout():
    scraper = AirCaraibesScraper()
    mock_page = AsyncMock()
    mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))

    price = await scraper.get_price(mock_page, "2026-12-28", "2027-01-15")
    assert price is None


@pytest.mark.asyncio
async def test_parse_price_strips_non_numeric():
    scraper = AirCaraibesScraper()
    assert scraper._parse_price("  487 €  ") == 487.0
    assert scraper._parse_price("1 234,50 €") == 1234.50
    assert scraper._parse_price("invalid") is None
```

- [ ] **Step 3: Run to verify they fail**

```bash
pytest tests/test_scrapers.py -v
```

Expected: `ImportError`.

- [ ] **Step 4: Create `scrapers/__init__.py`**

```python
```
(empty)

- [ ] **Step 5: Create `scrapers/base.py`**

```python
import asyncio
import random
from abc import ABC, abstractmethod
from typing import Optional

from playwright.async_api import Page


class AirlineScraper(ABC):
    name: str = ""

    async def get_price(self, page: Page, outbound: str, return_date: str) -> Optional[float]:
        try:
            return await self._fetch_price(page, outbound, return_date)
        except Exception as e:
            print(f"[{self.name}] Error ({outbound} → {return_date}): {e}")
            return None

    @abstractmethod
    async def _fetch_price(self, page: Page, outbound: str, return_date: str) -> Optional[float]:
        pass

    def _parse_price(self, text: str) -> Optional[float]:
        import re
        cleaned = re.sub(r"[^\d,.]", "", text.strip())
        cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    async def _random_delay(self):
        await asyncio.sleep(random.uniform(2.0, 5.0))
```

- [ ] **Step 6: Create `scrapers/air_caraibes.py`**

```python
from typing import Optional

from playwright.async_api import Page
from playwright_stealth import stealth_async

from scrapers.base import AirlineScraper

# Selectors identified by inspecting https://www.aircaribes.com
# Update these if the site structure changes
_PRICE_SELECTOR = ".price-lowest, [data-testid='lowest-price'], .fare-price"
_RESULTS_SELECTOR = ".flight-results, .search-results"


class AirCaraibesScraper(AirlineScraper):
    name = "Air Caraïbes"
    _BASE_URL = "https://www.aircaribes.com"

    async def _fetch_price(self, page: Page, outbound: str, return_date: str) -> Optional[float]:
        await stealth_async(page)
        await page.goto(self._BASE_URL, wait_until="networkidle", timeout=30000)
        await self._random_delay()

        # Fill origin
        await page.fill("[name='origin'], [placeholder*='Départ'], #origin", "ORY")
        await self._random_delay()

        # Fill destination
        await page.fill("[name='destination'], [placeholder*='Destination'], #destination", "FDF")
        await self._random_delay()

        # Fill outbound date (format: DD/MM/YYYY)
        d_out = _fmt_date(outbound)
        await page.fill("[name='departureDate'], [placeholder*='Aller'], #departureDate", d_out)

        # Fill return date
        d_ret = _fmt_date(return_date)
        await page.fill("[name='returnDate'], [placeholder*='Retour'], #returnDate", d_ret)

        await page.click("button[type='submit'], .search-button, #searchBtn")
        await page.wait_for_selector(_RESULTS_SELECTOR, timeout=30000)
        await self._random_delay()

        element = await page.query_selector(_PRICE_SELECTOR)
        if not element:
            return None

        text = await element.inner_text()
        return self._parse_price(text)


def _fmt_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"
```

- [ ] **Step 7: Run scraper tests — verify they pass**

```bash
pytest tests/test_scrapers.py::test_air_caraibes_returns_float_on_success tests/test_scrapers.py::test_scraper_returns_none_on_timeout tests/test_scrapers.py::test_parse_price_strips_non_numeric -v
```

Expected: 3 tests PASSED.

- [ ] **Step 8: Commit**

```bash
git add scrapers/ tests/test_scrapers.py
git commit -m "feat: base scraper and Air Caraïbes scraper"
```

---

## Task 6: Corsair scraper

**Files:**
- Create: `scrapers/corsair.py`

- [ ] **Step 1: Inspect Corsair site to identify selectors**

Open `https://www.corsair.fr` in a browser. Search for a round trip ORY → FDF. Open DevTools (F12) and identify:
- The form field names for origin, destination, departure date, return date
- The CSS selector for the lowest price displayed in results
- Note: Corsair uses FDF as destination code

- [ ] **Step 2: Implement `scrapers/corsair.py`**

```python
from typing import Optional

from playwright.async_api import Page
from playwright_stealth import stealth_async

from scrapers.base import AirlineScraper

# Selectors identified by inspecting https://www.corsair.fr
# Update these if the site structure changes
_PRICE_SELECTOR = ".price-amount, .total-price, [data-price], .fare-amount"
_RESULTS_SELECTOR = ".results-container, .flight-list, .offers-list"


class CorsairScraper(AirlineScraper):
    name = "Corsair"
    _BASE_URL = "https://www.corsair.fr"

    async def _fetch_price(self, page: Page, outbound: str, return_date: str) -> Optional[float]:
        await stealth_async(page)
        await page.goto(self._BASE_URL, wait_until="networkidle", timeout=30000)
        await self._random_delay()

        await page.fill("[name='origin'], [id*='origin'], [placeholder*='Départ']", "ORY")
        await self._random_delay()

        await page.fill("[name='destination'], [id*='destination'], [placeholder*='Destination']", "FDF")
        await self._random_delay()

        d_out = _fmt_date(outbound)
        await page.fill("[name='departDate'], [id*='depart'], [placeholder*='Aller']", d_out)

        d_ret = _fmt_date(return_date)
        await page.fill("[name='returnDate'], [id*='retour'], [placeholder*='Retour']", d_ret)

        await page.click("button[type='submit'], .btn-search, #searchFlights")
        await page.wait_for_selector(_RESULTS_SELECTOR, timeout=30000)
        await self._random_delay()

        element = await page.query_selector(_PRICE_SELECTOR)
        if not element:
            return None

        text = await element.inner_text()
        return self._parse_price(text)


def _fmt_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"
```

- [ ] **Step 3: Add Corsair test to `tests/test_scrapers.py`**

Add to end of `tests/test_scrapers.py`:

```python
@pytest.mark.asyncio
async def test_corsair_returns_none_on_missing_element():
    from scrapers.corsair import CorsairScraper
    scraper = CorsairScraper()
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.query_selector = AsyncMock(return_value=None)

    price = await scraper.get_price(mock_page, "2026-12-28", "2027-01-15")
    assert price is None
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_scrapers.py -v
```

Expected: 4 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add scrapers/corsair.py tests/test_scrapers.py
git commit -m "feat: Corsair scraper"
```

---

## Task 7: Air France scraper

**Files:**
- Create: `scrapers/air_france.py`

- [ ] **Step 1: Inspect Air France site to identify selectors**

Open `https://www.airfrance.fr` in a browser. Search for a round trip ORY → FDF. Open DevTools (F12) and identify:
- The URL structure (Air France often uses deep-link URLs for search: `https://www.airfrance.fr/search/...`)
- The CSS selector for the lowest price in results
- Note: Air France is a SPA — use `wait_for_load_state("networkidle")` and potentially intercept XHR responses

- [ ] **Step 2: Implement `scrapers/air_france.py`**

```python
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
            # Fallback: try the homepage form approach
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

        d_out = _fmt_date(outbound)
        await page.fill("[name='departureDate'], [aria-label*='Aller'], #departureDate", d_out)

        d_ret = _fmt_date(return_date)
        await page.fill("[name='returnDate'], [aria-label*='Retour'], #returnDate", d_ret)

        await page.click("button[type='submit'], [aria-label*='Rechercher'], .af-search-btn")
        await page.wait_for_selector(_RESULTS_SELECTOR, timeout=30000)
        await self._random_delay()

        element = await page.query_selector(_PRICE_SELECTOR)
        if not element:
            return None

        text = await element.inner_text()
        return self._parse_price(text)


def _fmt_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"
```

- [ ] **Step 3: Add Air France test**

Add to end of `tests/test_scrapers.py`:

```python
@pytest.mark.asyncio
async def test_air_france_parse_price():
    from scrapers.air_france import AirFranceScraper
    scraper = AirFranceScraper()
    assert scraper._parse_price("1 234 €") == 1234.0
    assert scraper._parse_price("€ 520,00") == 520.0
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_scrapers.py -v
```

Expected: 5 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add scrapers/air_france.py tests/test_scrapers.py
git commit -m "feat: Air France scraper"
```

---

## Task 8: Dashboard generator

**Files:**
- Create: `dashboard/__init__.py`
- Create: `dashboard/generator.py`
- Create: `tests/test_dashboard_generator.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_dashboard_generator.py`:

```python
import json
from core.price_store import PriceRecord
from dashboard.generator import generate_dashboard


def _records():
    return [
        PriceRecord("2026-10-01T08:00:00", "Air Caraïbes", "2026-12-28", "2027-01-15", 487.0),
        PriceRecord("2026-10-01T14:00:00", "Air Caraïbes", "2026-12-28", "2027-01-15", 465.0),
        PriceRecord("2026-10-01T08:00:00", "Corsair", "2026-12-28", "2027-01-15", 399.0),
        PriceRecord("2026-10-01T08:00:00", "Air France", "2026-12-29", "2027-01-16", 550.0),
    ]


def test_generate_returns_html_string():
    html = generate_dashboard(_records())
    assert isinstance(html, str)
    assert "<!DOCTYPE html" in html


def test_dashboard_contains_chart_js():
    html = generate_dashboard(_records())
    assert "chart.js" in html.lower() or "Chart" in html


def test_dashboard_contains_airline_names():
    html = generate_dashboard(_records())
    assert "Air Caraïbes" in html
    assert "Corsair" in html
    assert "Air France" in html


def test_dashboard_contains_price_data():
    html = generate_dashboard(_records())
    assert "487" in html
    assert "399" in html


def test_dashboard_contains_all_route_combos():
    html = generate_dashboard(_records())
    assert "2026-12-28" in html
    assert "2027-01-15" in html
    assert "2026-12-29" in html
    assert "2027-01-16" in html


def test_dashboard_shows_last_updated():
    html = generate_dashboard(_records())
    assert "Mis à jour" in html or "mise à jour" in html.lower()
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_dashboard_generator.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Create `dashboard/__init__.py`**

```python
```
(empty)

- [ ] **Step 4: Implement `dashboard/generator.py`**

```python
import json
from datetime import datetime
from pathlib import Path
from typing import List

from config import ROUTES
from core.price_store import PriceRecord

OUTPUT_PATH = Path(__file__).parent / "index.html"


def generate_dashboard(records: List[PriceRecord]) -> str:
    airlines = sorted({r.airline for r in records})
    colors = ["#1565c0", "#2e7d32", "#c62828", "#6a1b9a"]
    airline_colors = {a: colors[i % len(colors)] for i, a in enumerate(airlines)}

    charts_js = ""
    cards_html = ""

    for route in ROUTES:
        outbound = route["outbound"]
        ret = route["return"]
        combo_id = f"{outbound}_{ret}".replace("-", "")
        combo_label = f"{outbound} → {ret}"

        datasets = []
        for airline in airlines:
            pts = sorted(
                [r for r in records if r.airline == airline and r.outbound == outbound and r.return_date == ret],
                key=lambda r: r.timestamp,
            )
            if pts:
                labels = [r.timestamp[:16] for r in pts]
                prices = [r.price for r in pts]
                datasets.append({
                    "label": airline,
                    "data": prices,
                    "labels": labels,
                    "borderColor": airline_colors[airline],
                    "backgroundColor": airline_colors[airline] + "22",
                    "fill": False,
                    "tension": 0.3,
                })

        all_pts = [r for r in records if r.outbound == outbound and r.return_date == ret]
        current_by_airline = {}
        for airline in airlines:
            a_pts = [r for r in all_pts if r.airline == airline]
            if a_pts:
                current_by_airline[airline] = sorted(a_pts, key=lambda r: r.timestamp)[-1].price

        min_price = min((r.price for r in all_pts), default=0)
        max_price = max((r.price for r in all_pts), default=0)

        table_rows = ""
        for airline, price in current_by_airline.items():
            diff = price - min_price
            indicator = "🟢" if diff < 20 else ("🔴" if price >= max_price - 20 else "🟡")
            table_rows += f"<tr><td>{airline}</td><td><b>{price:.0f}€</b></td><td>{indicator}</td></tr>"

        all_labels = sorted({r.timestamp[:16] for r in all_pts})
        chart_datasets = json.dumps(datasets)

        charts_js += f"""
        (function() {{
            var ctx = document.getElementById('chart_{combo_id}').getContext('2d');
            var raw = {chart_datasets};
            var labels = {json.dumps(all_labels)};
            var datasets = raw.map(function(d) {{
                return {{
                    label: d.label,
                    data: labels.map(function(l) {{
                        var i = d.labels.indexOf(l);
                        return i >= 0 ? d.data[i] : null;
                    }}),
                    borderColor: d.borderColor,
                    backgroundColor: d.backgroundColor,
                    fill: d.fill,
                    tension: d.tension,
                    spanGaps: true,
                }};
            }});
            new Chart(ctx, {{
                type: 'line',
                data: {{ labels: labels, datasets: datasets }},
                options: {{
                    responsive: true,
                    plugins: {{ legend: {{ position: 'top' }} }},
                    scales: {{ y: {{ title: {{ display: true, text: 'Prix (€)' }} }} }}
                }}
            }});
        }})();
"""

        cards_html += f"""
        <div class="card">
            <h3>✈️ {combo_label}</h3>
            <canvas id="chart_{combo_id}" height="120"></canvas>
            <table>
                <thead><tr><th>Compagnie</th><th>Prix actuel</th><th>Statut</th></tr></thead>
                <tbody>{table_rows}</tbody>
            </table>
            <p class="meta">Min historique : {min_price:.0f}€ &nbsp;|&nbsp; Max : {max_price:.0f}€</p>
        </div>"""

    updated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>✈️ Prix Martinique</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #f5f5f5; margin: 0; padding: 16px; }}
    h1 {{ text-align: center; color: #1565c0; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; max-width: 1200px; margin: auto; }}
    @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    .card {{ background: white; border-radius: 8px; padding: 16px; box-shadow: 0 2px 4px rgba(0,0,0,.1); }}
    h3 {{ margin-top: 0; color: #1565c0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th {{ background: #1565c0; color: white; padding: 6px 8px; text-align: left; }}
    td {{ padding: 6px 8px; border-bottom: 1px solid #eee; }}
    .meta {{ color: #888; font-size: 12px; margin-top: 8px; }}
    .updated {{ text-align: center; color: #888; font-size: 13px; margin-top: 24px; }}
  </style>
</head>
<body>
  <h1>✈️ Suivi des prix Paris Orly → Martinique</h1>
  <div class="grid">{cards_html}</div>
  <p class="updated">Mis à jour le {updated_at}</p>
  <script>{charts_js}</script>
</body>
</html>"""


def write_dashboard(records: List[PriceRecord]) -> None:
    html = generate_dashboard(records)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"[dashboard] Written to {OUTPUT_PATH}")
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
pytest tests/test_dashboard_generator.py -v
```

Expected: 6 tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add dashboard/ tests/test_dashboard_generator.py
git commit -m "feat: dashboard generator with Chart.js and route summaries"
```

---

## Task 9: Main entry point

**Files:**
- Create: `main.py`

- [ ] **Step 1: Implement `main.py`**

```python
import asyncio
from typing import List, Optional

from playwright.async_api import async_playwright

from config import ROUTES
from core.alert_engine import Alert, detect_alert
from core.notifier import send_alert_email
from core.price_store import PriceRecord, append_price, load_prices
from dashboard.generator import write_dashboard
from scrapers.air_caraibes import AirCaraibesScraper
from scrapers.air_france import AirFranceScraper
from scrapers.corsair import CorsairScraper


async def run():
    scrapers = [AirCaraibesScraper(), CorsairScraper(), AirFranceScraper()]
    all_alerts: List[Alert] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        for scraper in scrapers:
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()

            for route in ROUTES:
                outbound = route["outbound"]
                ret = route["return"]

                price: Optional[float] = await scraper.get_price(page, outbound, ret)
                if price is None:
                    print(f"[main] No price for {scraper.name} {outbound}→{ret}")
                    continue

                print(f"[main] {scraper.name} {outbound}→{ret}: {price:.0f}€")

                records = load_prices()
                alert = detect_alert(records, scraper.name, outbound, ret, price)
                if alert:
                    print(f"[main] ALERT: {alert.airline} {alert.label}")
                    all_alerts.append(alert)

                append_price(scraper.name, outbound, ret, price)

            await context.close()

        await browser.close()

    records = load_prices()
    write_dashboard(records)

    if all_alerts:
        send_alert_email(all_alerts, records)
    else:
        print("[main] No alerts — prices stable.")


if __name__ == "__main__":
    asyncio.run(run())
```

- [ ] **Step 2: Run a dry test (no real network)**

```bash
python -c "from main import run; print('main.py imports OK')"
```

Expected: `main.py imports OK`

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: main orchestrator — scrape, alert, dashboard"
```

---

## Task 10: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/check_prices.yml`

- [ ] **Step 1: Create `.github/workflows/check_prices.yml`**

```yaml
name: Check Flight Prices

on:
  schedule:
    - cron: '0 * * * *'
  workflow_dispatch:

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

      - name: Cache Playwright browsers
        id: playwright-cache
        uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: playwright-chromium-${{ runner.os }}-${{ hashFiles('requirements.txt') }}

      - name: Install Playwright Chromium
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

- [ ] **Step 2: Add GitHub Secrets**

In your GitHub repo: Settings → Secrets and variables → Actions → New repository secret.
Add:
- `GMAIL_USER` → your Gmail address
- `GMAIL_APP_PASSWORD` → App Password generated at myaccount.google.com → Security → App passwords (requires 2FA enabled)
- `RECIPIENT_EMAIL` → email address to receive alerts

- [ ] **Step 3: Enable GitHub Actions on the repo**

Go to your repo on GitHub → Actions tab → enable workflows.

- [ ] **Step 4: Set up Netlify**

1. Go to app.netlify.com → Add new site → Import from Git
2. Connect your GitHub account, select the `martinique-tracker` repo
3. Build settings:
   - Build command: _(leave empty)_
   - Publish directory: `dashboard`
4. Deploy — Netlify will redeploy automatically on every push to `main`
5. Copy the Netlify URL (e.g. `https://martinique-tracker.netlify.app`)

- [ ] **Step 5: Trigger a manual run to verify**

In GitHub → Actions → "Check Flight Prices" → Run workflow.
Check the run logs to confirm:
- Scrapers execute without Python errors
- `prices.json` is committed and pushed
- `dashboard/index.html` is updated
- Netlify redeploys within ~1 minute

- [ ] **Step 6: Commit workflow file**

```bash
git add .github/workflows/check_prices.yml
git commit -m "feat: GitHub Actions hourly cron with Playwright cache"
git push
```

---

## Task 11: Full test suite

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: all tests PASS. If any fail, fix before proceeding.

- [ ] **Step 2: Check test coverage on core modules**

```bash
pip install pytest-cov
pytest tests/ --cov=core --cov=dashboard --cov-report=term-missing
```

Expected: `core/price_store.py`, `core/alert_engine.py`, `core/notifier.py`, `dashboard/generator.py` all above 80%.

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "chore: complete test suite passes"
git push
```

---

## Self-Review Against Spec

| Spec requirement | Covered by |
|-----------------|------------|
| Scrape Air France, Air Caraïbes, Corsair | Tasks 5, 6, 7 |
| ORY → FDF, 4 date combinations | `config.py` Task 1 |
| Alert threshold > 20€ | Task 3, `core/alert_engine.py` |
| Email HTML + PDF attachment | Task 4, `core/notifier.py` |
| Chart.js dashboard (4 graphs, table, indicators) | Task 8, `dashboard/generator.py` |
| Hourly GitHub Actions cron | Task 10, workflow file |
| Private GitHub repo + Netlify dashboard | Task 10, Netlify setup step |
| `prices.json` versioned history | Tasks 2, 10 |
| Gmail SMTP via env vars / GitHub Secrets | Tasks 4, 10 |
| Playwright stealth + random delays | Tasks 5, 6, 7 |
| Baseline: no alert on first record | Task 3 |
