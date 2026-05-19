"""Inspecte la structure HTML du calendrier Google Flights."""
import asyncio
from playwright.async_api import async_playwright
from scrapers.google_flights import _fill_form

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
)


async def debug():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=UA, locale="fr-FR", timezone_id="Europe/Paris",
        )
        await ctx.add_cookies([{
            "name": "SOCS",
            "value": "CAESEwgDEgk2NzI4MDkwNjYaAmZyIAEaBgiA_LilBg",
            "domain": ".google.com",
            "path": "/",
        }])
        page = await ctx.new_page()
        await page.goto("https://www.google.com/travel/flights", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # Remplir seulement origine + destination pour ouvrir le calendrier
        origin = page.locator('input[aria-label="De"]').first
        await origin.click()
        await page.wait_for_timeout(1000)
        await page.keyboard.press("Control+a")
        await page.keyboard.press("Delete")
        await page.wait_for_timeout(500)
        await page.keyboard.type("Paris-Orly", delay=100)
        await page.wait_for_timeout(2000)
        ory = page.locator('[role="option"]', has_text="ORY")
        await ory.first.wait_for(state="visible", timeout=8000)
        await ory.first.click()
        await page.wait_for_timeout(500)

        dest = page.locator('input[aria-label="À "]').first
        await dest.click()
        await page.wait_for_timeout(1000)
        await page.keyboard.press("Control+a")
        await page.keyboard.press("Delete")
        await page.wait_for_timeout(500)
        await page.keyboard.type("Fort-de-France", delay=100)
        await page.wait_for_timeout(2000)
        fdf = page.locator('[role="option"]', has_text="FDF")
        await fdf.first.wait_for(state="visible", timeout=8000)
        await fdf.first.click()
        await page.wait_for_timeout(2000)  # Laisser le calendrier s'ouvrir

        await page.screenshot(path="debug_calendar_open.png")
        print("[debug] Screenshot : debug_calendar_open.png")

        info = await page.evaluate(r"""
        () => {
            const result = {
                nextBtns: [],
                dateCells: [],
                okBtns: [],
            };

            // Boutons de navigation
            document.querySelectorAll('button').forEach(btn => {
                const aria = btn.getAttribute('aria-label') || '';
                const text = btn.innerText.trim();
                if (aria.toLowerCase().includes('suivant') || aria.toLowerCase().includes('next') ||
                    aria.toLowerCase().includes('précédent') || aria.toLowerCase().includes('prev')) {
                    result.nextBtns.push({ text, ariaLabel: aria, jsname: btn.getAttribute('jsname') });
                }
                if (text === 'OK') result.okBtns.push({ ariaLabel: aria, jsname: btn.getAttribute('jsname') });
            });

            // Cellules de dates (regarder les 3 premières)
            const cells = document.querySelectorAll('[data-iso], [data-date], td[role="button"], div[role="button"][aria-label]');
            let count = 0;
            cells.forEach(el => {
                if (count >= 5) return;
                const rect = el.getBoundingClientRect();
                if (rect.width === 0) return;
                result.dateCells.push({
                    tag: el.tagName,
                    dataIso: el.getAttribute('data-iso'),
                    dataDate: el.getAttribute('data-date'),
                    ariaLabel: el.getAttribute('aria-label'),
                    role: el.getAttribute('role'),
                    text: el.innerText.trim().slice(0, 30),
                });
                count++;
            });

            return result;
        }
        """)

        print(f"\n=== Boutons navigation ({len(info['nextBtns'])}) ===")
        for b in info["nextBtns"]:
            print(f"  {b}")

        print(f"\n=== Boutons OK ({len(info['okBtns'])}) ===")
        for b in info["okBtns"]:
            print(f"  {b}")

        print(f"\n=== Cellules dates ({len(info['dateCells'])}) ===")
        for c in info["dateCells"]:
            print(f"  {c}")

        await ctx.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
