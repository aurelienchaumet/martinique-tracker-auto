"""Teste si le dialog calendrier s'ouvre automatiquement après FDF."""
import asyncio
from playwright.async_api import async_playwright

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
DIALOG = '[role="dialog"][aria-modal="true"]:has(input[aria-label="Départ"])'


async def run():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent=UA, locale="fr-FR", timezone_id="Europe/Paris")
        await ctx.add_cookies([{"name": "SOCS", "value": "CAESEwgDEgk2NzI4MDkwNjYaAmZyIAEaBgiA_LilBg",
                                "domain": ".google.com", "path": "/"}])
        page = await ctx.new_page()
        await page.goto("https://www.google.com/travel/flights", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # ORY
        o = page.locator('input[aria-label="De"]').first
        await o.click(); await page.wait_for_timeout(1000)
        await page.keyboard.press("Control+a"); await page.keyboard.press("Delete")
        await page.wait_for_timeout(500)
        await page.keyboard.type("Paris-Orly", delay=100); await page.wait_for_timeout(2000)
        await page.locator('[role="option"]', has_text="ORY").first.wait_for(state="visible", timeout=8000)
        await page.locator('[role="option"]', has_text="ORY").first.click()
        await page.wait_for_timeout(500)
        print("ORY OK")

        # FDF
        dest = page.locator('input[aria-label="À "]').first
        await dest.click(); await page.wait_for_timeout(1000)
        await page.keyboard.press("Control+a"); await page.keyboard.press("Delete")
        await page.wait_for_timeout(500)
        await page.keyboard.type("Fort-de-France", delay=100); await page.wait_for_timeout(2000)
        await page.locator('[role="option"]', has_text="FDF").first.wait_for(state="visible", timeout=8000)
        await page.locator('[role="option"]', has_text="FDF").first.click()
        print("FDF clicked")

        # Tester si le dialog s'ouvre automatiquement
        for wait_s in range(1, 8):
            await page.wait_for_timeout(1000)
            vis = await page.locator(DIALOG).is_visible()
            print(f"Dialog visible après {wait_s}s : {vis}")
            if vis:
                break

        await page.screenshot(path="debug_after_fdf.png")

        # Vérifier l'état de la page
        url = page.url
        print(f"URL : {url}")
        form_vals = await page.evaluate("""
        () => [...document.querySelectorAll('input[aria-label="De"], input[aria-label="À "]')]
              .map(i => ({label: i.getAttribute('aria-label'), value: i.value}))
        """)
        print(f"Valeurs form : {form_vals}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
