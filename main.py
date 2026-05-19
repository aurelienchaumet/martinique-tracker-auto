from typing import List

from config import ROUTES
from core.alert_engine import Alert, detect_alert
from core.notifier import send_alert_email
from core.price_store import append_price, load_prices
from dashboard.generator import write_dashboard
from scrapers.google_flights import GoogleFlightsScraper


def run():
    scraper = GoogleFlightsScraper()
    all_alerts: List[Alert] = []

    for route in ROUTES:
        outbound = route["outbound"]
        ret = route["return"]

        prices = scraper.get_prices(outbound, ret)
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

    records = load_prices()
    write_dashboard(records)

    if all_alerts:
        send_alert_email(all_alerts, records)
    else:
        print("[main] Aucune alerte — prix stables.")


if __name__ == "__main__":
    run()
