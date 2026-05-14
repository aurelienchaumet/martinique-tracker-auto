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
