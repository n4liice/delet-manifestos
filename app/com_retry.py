import asyncio

from . import config
from .logger import log
from .screenshot import screenshot_erro


async def com_retry(nome_etapa, fn, page, max_tentativas=None):
    max_tentativas = max_tentativas or config.MAX_RETRIES
    ultimo_erro = None

    for tentativa in range(1, max_tentativas + 1):
        try:
            log(nome_etapa, f"Tentativa {tentativa}/{max_tentativas}")
            return await fn()
        except Exception as erro:
            ultimo_erro = erro
            log(nome_etapa, f"Falhou: {erro}", "WARN")
            if tentativa == max_tentativas:
                await screenshot_erro(page, nome_etapa)
            else:
                await page.wait_for_timeout(1000 * tentativa)

    raise RuntimeError(f"[{nome_etapa}] Falha apos {max_tentativas} tentativas: {ultimo_erro}")
