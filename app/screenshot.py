import os
import time

from . import config
from .logger import log


async def screenshot_erro(page, etapa):
    os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
    arquivo = os.path.join(config.SCREENSHOT_DIR, f"erro_{etapa}_{int(time.time() * 1000)}.png")
    try:
        await page.screenshot(path=arquivo, full_page=True)
        log(etapa, f"Screenshot salvo em {arquivo}", "ERROR")
        return arquivo
    except Exception as e:
        log(etapa, f"Falha ao salvar screenshot: {e}", "ERROR")
        return None
