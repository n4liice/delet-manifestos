import asyncio
import sys

from playwright.async_api import async_playwright

from app import config
from app.excluir_manifesto import executar_exclusao
from app.logger import log


async def login(page):
    await page.goto(f"{config.URL_BASE}/manifests", timeout=config.TIMEOUT_PADRAO)
    await page.wait_for_load_state("networkidle")

    if "/sign_in" in page.url:
        log("login", "Sessao expirada. Fazendo login...")
        await page.fill("input[name='user[email]']", config.EMAIL)
        await page.fill("input[name='user[password]']", config.SENHA)
        await page.click("input[type='submit'], button:has-text('Entrar')")
        await page.wait_for_url("**/manifests**", timeout=config.TIMEOUT_PADRAO)
        log("login", "Login realizado.")
    else:
        log("login", "Sessao ativa.")


async def main():
    numero_manifesto = sys.argv[1] if len(sys.argv) > 1 else "119441"
    motivo = sys.argv[2] if len(sys.argv) > 2 else "TESTE DE CRIAÇÃOO"
    confirmar = len(sys.argv) > 3 and sys.argv[3].lower() == "true"

    log("main", f"numeroManifesto={numero_manifesto} motivo={motivo!r} confirmar={confirmar}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.HEADLESS)
        page = await browser.new_page()

        try:
            await login(page)
            resultado = await executar_exclusao(page, numero_manifesto, motivo, confirmar)
            log("main", f"Resultado final: {resultado}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
