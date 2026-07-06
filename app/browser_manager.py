import asyncio

from playwright.async_api import async_playwright

from . import config
from .logger import log

_playwright = None
_browser = None
_context = None
_page = None
_lock = asyncio.Lock()


async def _iniciar():
    global _playwright, _browser, _context, _page

    if _page is not None and not _page.is_closed():
        return

    if _playwright is None:
        _playwright = await async_playwright().start()

    if _browser is None or not _browser.is_connected():
        _browser = await _playwright.chromium.launch(headless=config.HEADLESS)
        log("browser_manager", "Browser iniciado.")

    _context = await _browser.new_context()
    _page = await _context.new_page()
    log("browser_manager", "Contexto/pagina criados.")


async def login():
    await _page.goto(f"{config.URL_BASE}/manifests", timeout=config.TIMEOUT_PADRAO)
    await _page.wait_for_load_state("networkidle")

    if "/sign_in" in _page.url:
        log("login", "Sessao expirada. Fazendo login...")
        await _page.fill("input[name='user[email]']", config.EMAIL)
        await _page.fill("input[name='user[password]']", config.SENHA)
        await _page.click("input[type='submit'], button:has-text('Entrar')")
        await _page.wait_for_url("**/manifests**", timeout=config.TIMEOUT_PADRAO)
        log("login", "Login realizado.")
    else:
        log("login", "Sessao ativa.")


async def executar(tarefa):
    # Serializa: so uma automacao roda por vez sobre o mesmo page/context compartilhado
    async with _lock:
        await _iniciar()
        await login()
        return await tarefa(_page)


async def encerrar():
    global _browser, _context, _page, _playwright

    if _browser is not None:
        await _browser.close()
        _browser = None
        _context = None
        _page = None

    if _playwright is not None:
        await _playwright.stop()
        _playwright = None
