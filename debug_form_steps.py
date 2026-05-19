"""Debug pas-à-pas : screenshot à chaque étape du remplissage formulaire."""
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

        print("[1] Chargement de la page...")
        await page.goto("https://www.google.com/travel/flights", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="step1_loaded.png")
        print("[1] step1_loaded.png")

        print("[2] Clic sur le champ origine (input[aria-label='De'])...")
        origin = page.locator('input[aria-label="De"]').first
        await origin.click()
        await page.wait_for_timeout(1000)
        await page.screenshot(path="step2_origin_focused.png")
        print("[2] step2_origin_focused.png")

        # Voir quel élément a le focus
        focused = await page.evaluate("() => { const el = document.activeElement; return { tag: el.tagName, ariaLabel: el.getAttribute('aria-label'), value: el.value }; }")
        print(f"[2] Élément actif : {focused}")

        print("[3] Sélection tout + suppression...")
        await page.keyboard.press("Control+a")
        await page.keyboard.press("Delete")
        await page.wait_for_timeout(500)

        print("[4] Saisie 'Paris'...")
        await page.keyboard.type("Paris", delay=100)
        await page.wait_for_timeout(2000)
        await page.screenshot(path="step4_typed_paris.png")
        print("[4] step4_typed_paris.png")

        # Lister ce qui est apparu
        appeared = await page.evaluate("""
        () => {
            const result = [];
            // Chercher tous les éléments avec role=option qui sont visibles
            document.querySelectorAll('[role="option"]').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    result.push({
                        role: 'option',
                        text: el.innerText.trim().slice(0, 80),
                        visible: true,
                        dataValue: el.getAttribute('data-value'),
                        class: el.className.slice(0, 60)
                    });
                }
            });
            // Aussi chercher les listbox
            document.querySelectorAll('[role="listbox"] li, [role="listbox"] [role="option"]').forEach(el => {
                const rect = el.getBoundingClientRect();
                result.push({
                    role: 'listbox-item',
                    text: el.innerText.trim().slice(0, 80),
                    visible: rect.width > 0,
                });
            });
            return result;
        }
        """)
        print(f"[4] Éléments apparus après saisie 'Paris' : {len(appeared)}")
        for el in appeared[:10]:
            print(f"     {el}")

        print("[5] Saisie 'Orly' en plus...")
        await page.keyboard.type("-Orly", delay=100)
        await page.wait_for_timeout(2000)
        await page.screenshot(path="step5_typed_orly.png")
        print("[5] step5_typed_orly.png")

        appeared2 = await page.evaluate("""
        () => {
            const result = [];
            document.querySelectorAll('[role="option"]').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    result.push({ text: el.innerText.trim().slice(0, 80), visible: true });
                }
            });
            return result;
        }
        """)
        print(f"[5] Options visibles après 'Paris-Orly' : {appeared2}")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
