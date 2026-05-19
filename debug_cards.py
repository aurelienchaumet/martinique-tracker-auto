"""Debug : structure des cartes de vol (parent de div[data-gs])."""
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
        await page.goto("https://www.google.com/travel/flights", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await _fill_form(page, "2026-12-28", "2027-01-15")
        await page.wait_for_timeout(15000)
        print(f"URL : {page.url}")

        # Pour chaque div[data-gs] avec un prix, remonter jusqu'au li ancêtre et afficher son texte
        cards = await page.evaluate(r"""
        () => {
            const results = [];
            const seen = new Set();

            document.querySelectorAll('div[data-gs]').forEach(priceEl => {
                const price = priceEl.innerText.trim();
                if (!price.includes('€')) return;

                // Remonter jusqu'au li ancêtre
                const li = priceEl.closest('li');
                if (!li) return;

                const key = li.className.slice(0, 40);
                if (seen.has(key + price)) return;
                seen.add(key + price);

                results.push({
                    price: price,
                    liClass: li.className.slice(0, 80),
                    liText: li.innerText.trim().slice(0, 300),
                });
            });
            return results.slice(0, 5);
        }
        """)

        if cards:
            print(f"\n=== {len(cards)} cartes trouvées ===")
            for c in cards:
                print(f"\n--- Prix: {c['price']} ---")
                print(f"  li.class = {c['liClass']!r}")
                print(f"  li.text  = {c['liText']!r}")
        else:
            print("\nAucune carte trouvée via closest('li') — tentative sans li...")
            # Essai sans li
            fallback = await page.evaluate(r"""
            () => {
                const results = [];
                document.querySelectorAll('div[data-gs]').forEach((priceEl, i) => {
                    if (i >= 3) return;
                    const price = priceEl.innerText.trim();
                    if (!price.includes('€')) return;
                    // Remonter 6 niveaux
                    let el = priceEl;
                    const chain = [];
                    for (let j = 0; j < 6; j++) {
                        el = el.parentElement;
                        if (!el) break;
                        chain.push({ tag: el.tagName, cls: el.className.slice(0, 50) });
                    }
                    results.push({ price, chain });
                });
                return results;
            }
            """)
            for fb in fallback:
                print(f"\nPrix: {fb['price']}")
                for j, step in enumerate(fb["chain"]):
                    print(f"  +{j+1}: {step['tag']} class={step['cls']!r}")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
