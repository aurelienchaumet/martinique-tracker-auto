"""Inspecte le dialog de dates étape par étape."""
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

        # Origine
        o = page.locator('input[aria-label="De"]').first
        await o.click(); await page.wait_for_timeout(1000)
        await page.keyboard.press("Control+a"); await page.keyboard.press("Delete")
        await page.wait_for_timeout(500)
        await page.keyboard.type("Paris-Orly", delay=100); await page.wait_for_timeout(2000)
        await page.locator('[role="option"]', has_text="ORY").first.wait_for(state="visible", timeout=8000)
        await page.locator('[role="option"]', has_text="ORY").first.click()
        await page.wait_for_timeout(500)
        print("[1] ORY sélectionné")

        # Destination
        dest = page.locator('input[aria-label="À "]').first
        await dest.click(); await page.wait_for_timeout(1000)
        await page.keyboard.press("Control+a"); await page.keyboard.press("Delete")
        await page.wait_for_timeout(500)
        await page.keyboard.type("Fort-de-France", delay=100); await page.wait_for_timeout(2000)
        await page.locator('[role="option"]', has_text="FDF").first.wait_for(state="visible", timeout=8000)
        await page.locator('[role="option"]', has_text="FDF").first.click()
        await page.wait_for_timeout(1000)
        print("[2] FDF sélectionné")

        # État du dialog
        vis = await page.locator(DIALOG).is_visible()
        print(f"[3] Dialog visible après FDF : {vis}")

        if not vis:
            print("[3] Clic sur input Départ pour ouvrir le dialog...")
            await page.locator('input[aria-label="Départ"]').first.click()
            await page.wait_for_timeout(800)
            vis = await page.locator(DIALOG).is_visible()
            print(f"[3] Dialog visible après clic Départ : {vis}")

        await page.screenshot(path="debug_dialog_step3.png")

        # Lister tous les inputs du dialog
        inputs_info = await page.evaluate("""
        () => {
            const dialogs = document.querySelectorAll('[role="dialog"][aria-modal="true"]');
            const result = [];
            dialogs.forEach((dlg, i) => {
                const inputs = [...dlg.querySelectorAll('input')].map(inp => ({
                    label: inp.getAttribute('aria-label'),
                    placeholder: inp.placeholder,
                    value: inp.value,
                    visible: inp.offsetParent !== null,
                }));
                if (inputs.length > 0) {
                    result.push({ dialogIndex: i, ariaLabel: dlg.getAttribute('aria-label'), inputs });
                }
            });
            return result;
        }
        """)
        print(f"[4] Dialogs avec inputs : {len(inputs_info)}")
        for d in inputs_info:
            print(f"   Dialog {d['dialogIndex']} aria-label={d['ariaLabel']!r} : {d['inputs']}")

        if vis:
            print("[5] Saisie dates dans le dialog...")
            dlg_depart = page.locator(f'{DIALOG} input[aria-label="Départ"]')
            await dlg_depart.click()
            await page.wait_for_timeout(300)
            await page.keyboard.press("Control+a")
            await page.keyboard.press("Delete")
            await page.keyboard.type("28/12/2026", delay=80)
            await page.wait_for_timeout(600)

            await page.keyboard.press("Tab")
            await page.wait_for_timeout(300)
            await page.keyboard.press("Control+a")
            await page.keyboard.press("Delete")
            await page.keyboard.type("15/01/2027", delay=80)
            await page.wait_for_timeout(600)

            # État des inputs après saisie
            vals = await page.evaluate("""
            () => {
                return [...document.querySelectorAll('input[aria-label="Départ"], input[aria-label="Retour"]')]
                    .map(i => ({label: i.getAttribute('aria-label'), value: i.value}));
            }
            """)
            print(f"[5] Valeurs inputs après saisie : {vals}")

            await page.screenshot(path="debug_dialog_step5.png")

            # Clic OK
            ok = page.locator('button[jsname="McfNlf"]').first
            await ok.click()
            await page.wait_for_timeout(3000)
            print(f"[6] URL après OK : {page.url[:100]}")
            await page.screenshot(path="debug_dialog_step6.png")

        await ctx.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
