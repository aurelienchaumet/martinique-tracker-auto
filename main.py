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
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
)


async def run():
    scraper = GoogleFlightsScraper()
    all_alerts: List[Alert] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=UA,
            locale="fr-FR",
            timezone_id="Europe/Paris",
        )
        # Cookie SOCS pour bypass consentement Google (RGPD)
        await context.add_cookies([{
            "name": "SOCS",
            "value": "CAESEwgDEgk2NzI4MDkwNjYaAmZyIAEaBgiA_LilBg",
            "domain": ".google.com",
            "path": "/",
        }])
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
