"""Liste tous les inputs et comboboxes sur Google Flights pour trouver les bons sélecteurs."""
import asyncio
from playwright.async_api import async_playwright

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
        await page.wait_for_timeout(3000)
        await page.screenshot(path="debug_initial.png")

        info = await page.evaluate("""
        () => {
            const result = { inputs: [], comboboxes: [], buttons: [] };

            // Tous les inputs
            document.querySelectorAll('input').forEach((el, i) => {
                result.inputs.push({
                    index: i,
                    type: el.type,
                    value: el.value.slice(0, 50),
                    placeholder: el.placeholder,
                    ariaLabel: el.getAttribute('aria-label'),
                    name: el.name,
                    id: el.id,
                    jsname: el.getAttribute('jsname'),
                    className: el.className.slice(0, 60),
                });
            });

            // Éléments avec role="combobox"
            document.querySelectorAll('[role="combobox"]').forEach((el, i) => {
                result.comboboxes.push({
                    index: i,
                    tag: el.tagName,
                    ariaLabel: el.getAttribute('aria-label'),
                    placeholder: el.getAttribute('placeholder'),
                    value: el.value || el.innerText.slice(0, 50),
                    jsname: el.getAttribute('jsname'),
                    className: el.className.slice(0, 60),
                });
            });

            // Boutons de recherche
            document.querySelectorAll('button').forEach((el, i) => {
                const text = el.innerText.trim().slice(0, 40);
                if (text) result.buttons.push({ index: i, text, ariaLabel: el.getAttribute('aria-label') });
            });

            return result;
        }
        """)

        print("\n=== INPUTS ===")
        for inp in info["inputs"]:
            print(f"  [{inp['index']}] type={inp['type']!r} value={inp['value']!r} "
                  f"placeholder={inp['placeholder']!r} aria-label={inp['ariaLabel']!r} "
                  f"jsname={inp['jsname']!r}")

        print("\n=== COMBOBOXES ===")
        for cb in info["comboboxes"]:
            print(f"  [{cb['index']}] tag={cb['tag']} aria-label={cb['ariaLabel']!r} "
                  f"placeholder={cb['placeholder']!r} value={cb['value']!r} jsname={cb['jsname']!r}")

        print("\n=== BOUTONS ===")
        for btn in info["buttons"]:
            print(f"  [{btn['index']}] text={btn['text']!r} aria-label={btn['ariaLabel']!r}")

        print("\n[debug] Screenshot initial sauvé : debug_initial.png")
        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
