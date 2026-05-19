"""Script de debug : screenshot + HTML dump pour diagnostiquer les sélecteurs."""
import asyncio
import sys

from playwright.async_api import async_playwright

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
)

URL = (
    "https://www.google.com/travel/flights"
    "#flt=ORY.FDF.2026-12-28*FDF.ORY.2027-01-15"
    ";c:EUR;e:1;sd:1;t:f"
)


async def debug():
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

        print(f"[debug] Chargement : {URL}")
        await page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        print(f"[debug] URL après redirection : {page.url}")

        # Attendre que le JS s'exécute
        await page.wait_for_timeout(5000)

        # Screenshot
        await page.screenshot(path="debug_screenshot.png", full_page=True)
        print("[debug] Screenshot sauvé : debug_screenshot.png")

        # Sauvegarder le HTML
        html = await page.content()
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("[debug] HTML sauvé : debug_page.html")

        # Chercher des éléments qui ressemblent à des prix
        price_candidates = await page.evaluate("""
        () => {
            const results = [];
            // Chercher tous les éléments <li> avec un attribut data-*
            document.querySelectorAll('li[class]').forEach(el => {
                const text = el.innerText.trim().slice(0, 100);
                if (text.includes('€') || text.includes('EUR')) {
                    results.push({
                        class: el.className,
                        text: text.slice(0, 120)
                    });
                }
            });
            return results.slice(0, 10);
        }
        """)

        if price_candidates:
            print(f"\n[debug] {len(price_candidates)} éléments <li> avec prix trouvés :")
            for c in price_candidates:
                print(f"  class={c['class']!r}  text={c['text']!r}")
        else:
            print("[debug] Aucun <li> avec € trouvé — la page ne contient pas de résultats de vol")

        # Lister tous les <li> avec data-gs ou similaire
        li_attrs = await page.evaluate("""
        () => {
            const attrs = new Set();
            document.querySelectorAll('li').forEach(el => {
                for (const attr of el.attributes) {
                    if (attr.name.startsWith('data-')) attrs.add(attr.name);
                }
            });
            return [...attrs];
        }
        """)
        if li_attrs:
            print(f"\n[debug] Attributs data-* trouvés sur <li> : {li_attrs}")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
