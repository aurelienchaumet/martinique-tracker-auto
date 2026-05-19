"""Debug : inspecte les éléments de résultats après la recherche Google Flights."""
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
        context = await browser.new_context(
            user_agent=UA, locale="fr-FR", timezone_id="Europe/Paris",
        )
        await context.add_cookies([{
            "name": "SOCS",
            "value": "CAESEwgDEgk2NzI4MDkwNjYaAmZyIAEaBgiA_LilBg",
            "domain": ".google.com",
            "path": "/",
        }])
        page = await context.new_page()

        print("[1] Chargement...")
        await page.goto("https://www.google.com/travel/flights", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        print("[2] Remplissage formulaire...")
        await _fill_form(page, "2026-12-28", "2027-01-15")

        print("[3] Attente des résultats (15s)...")
        await page.wait_for_timeout(15000)
        await page.screenshot(path="debug_results_full.png", full_page=True)
        print("[3] Screenshot : debug_results_full.png")
        print(f"[3] URL : {page.url}")

        info = await page.evaluate(r"""
        () => {
            const result = { dataGs: [], liElements: [], priceTexts: [] };

            // Éléments avec data-gs
            document.querySelectorAll('[data-gs]').forEach((el, i) => {
                if (i >= 10) return;
                result.dataGs.push({
                    tag: el.tagName,
                    class: el.className.slice(0, 60),
                    ariaLabel: el.getAttribute('aria-label'),
                    text: el.innerText.trim().slice(0, 100),
                    dataGs: el.getAttribute('data-gs').slice(0, 30),
                });
            });

            // Tous les <li> avec une class
            document.querySelectorAll('li[class]').forEach((el, i) => {
                if (i >= 10) return;
                const text = el.innerText.trim().slice(0, 80);
                if (text.length > 5) {
                    result.liElements.push({
                        class: el.className.slice(0, 60),
                        text: text,
                        hasDataGs: el.hasAttribute('data-gs'),
                    });
                }
            });

            // Textes avec € visibles
            document.querySelectorAll('*').forEach(el => {
                if (result.priceTexts.length >= 10) return;
                const text = el.innerText;
                if (el.children.length === 0 && text && text.includes('€')) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0) {
                        result.priceTexts.push({
                            tag: el.tagName,
                            class: el.className.slice(0, 50),
                            text: text.trim().slice(0, 50),
                        });
                    }
                }
            });

            return result;
        }
        """)

        print(f"\n=== [data-gs] ({len(info['dataGs'])} éléments) ===")
        for el in info["dataGs"]:
            print(f"  {el['tag']} class={el['class']!r} aria={el['ariaLabel']!r} text={el['text']!r}")

        print(f"\n=== <li> avec class ({len(info['liElements'])} éléments) ===")
        for el in info["liElements"]:
            print(f"  class={el['class']!r} data-gs={el['hasDataGs']} text={el['text']!r}")

        print(f"\n=== Textes avec € ({len(info['priceTexts'])} éléments) ===")
        for el in info["priceTexts"]:
            print(f"  {el['tag']} class={el['class']!r} text={el['text']!r}")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
