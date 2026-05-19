"""Script de debug : teste le remplissage du formulaire Google Flights."""
import asyncio
import sys

from playwright.async_api import async_playwright
from scrapers.google_flights import GoogleFlightsScraper

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
)


async def debug():
    scraper = GoogleFlightsScraper()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=UA,
            locale="fr-FR",
            timezone_id="Europe/Paris",
        )
        await context.add_cookies([{
            "name": "SOCS",
            "value": "CAESEwgDEgk2NzI4MDkwNjYaAmZyIAEaBgiA_LilBg",
            "domain": ".google.com",
            "path": "/",
        }])
        page = await context.new_page()

        print("[debug] Test remplissage formulaire pour 2026-12-28 → 2027-01-15")
        prices = await scraper.get_prices(page, "2026-12-28", "2027-01-15")

        if prices:
            print(f"\n[debug] Succès ! {len(prices)} compagnies trouvées :")
            for airline, price in prices.items():
                print(f"  {airline}: {price:.0f}€")
        else:
            print("\n[debug] Aucun prix trouvé — screenshot sauvé si erreur")
            await page.screenshot(path="debug_screenshot_final.png", full_page=True)
            print("[debug] Screenshot : debug_screenshot_final.png")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
