import re

from playwright.async_api import expect

from . import config
from .com_retry import com_retry
from .logger import log
from .screenshot import screenshot_erro


# Etapa 1: navega ate Manifestos
async def abrir_manifestos(page):
    async def tarefa():
        await page.goto(f"{config.URL_BASE}/manifests", timeout=config.TIMEOUT_PADRAO)
        await page.wait_for_load_state("networkidle")
        await expect(page).to_have_url(re.compile("manifests"))
        await expect(page.get_by_role("textbox", name="Número")).to_be_visible(timeout=config.TIMEOUT_PADRAO)

    await com_retry("abrir_manifestos", tarefa, page)


# Etapa 2: limpa o filtro de Data
async def limpar_filtro_data(page):
    async def tarefa():
        campo_data = page.get_by_role("textbox", name="Data")
        await campo_data.click()
        btn_limpar = page.get_by_role("button", name="Limpar")
        await expect(btn_limpar).to_be_visible(timeout=config.TIMEOUT_PADRAO)
        await btn_limpar.click()
        await expect(campo_data).to_have_value("")

    await com_retry("limpar_filtro_data", tarefa, page)


# Etapa 3: preenche o numero e pesquisa com Enter
async def pesquisar_manifesto(page, numero):
    async def tarefa():
        campo_numero = page.get_by_role("textbox", name="Número")
        await campo_numero.fill("")
        await campo_numero.fill(numero)
        await expect(campo_numero).to_have_value(numero)

        await campo_numero.press("Enter")

        # "table tbody tr" generico pegava linhas de outra tabela (autocomplete/dropdown)
        # que sempre tem ~23 itens, sem relacao com o filtro de manifestos. As linhas reais
        # da tabela de manifestos tem a classe "vue-item" (confirmado via inspecao do DOM).
        linhas = page.locator("tr.vue-item")
        await expect(linhas).to_have_count(1, timeout=config.TIMEOUT_PADRAO)
        await expect(linhas).to_contain_text(numero)

    await com_retry("pesquisar_manifesto", tarefa, page)


# Etapa 4: abre o menu de acoes da linha, rola ate "Excluir" e clica
async def abrir_menu_e_excluir(page, numero):
    async def tarefa():
        linha = page.locator("tr.vue-item", has_text=numero)
        btn_dropdown = linha.locator("button:has(i.fa-angle-down)")
        await btn_dropdown.click()

        # Escopado na propria linha - ".last" na pagina inteira podia pegar outro
        # dropdown (notificacao, avatar, etc.), nao o que abriu para esse manifesto.
        menu = linha.locator("ul.dropdown-menu")
        await expect(menu).to_be_visible(timeout=config.TIMEOUT_PADRAO)

        item_excluir = menu.locator("li[title='Excluir']")
        await item_excluir.scroll_into_view_if_needed()
        await expect(item_excluir).to_be_visible()
        await item_excluir.click()

        modal = page.locator("text=Confirma a exclusão do registro?")
        await expect(modal).to_be_visible(timeout=config.TIMEOUT_PADRAO)

    await com_retry("abrir_menu_e_excluir", tarefa, page)


# Etapa 5: preenche o motivo e (se confirmar=True) efetiva a exclusao
async def confirmar_exclusao(page, motivo, confirmar):
    if not motivo or len(motivo.strip()) < 15:
        raise ValueError("Motivo invalido: precisa ter no minimo 15 caracteres (regra do sistema).")

    campo_motivo = page.get_by_placeholder("motivo: mínimo 15 caracteres")
    await campo_motivo.fill(motivo)
    await expect(campo_motivo).to_have_value(motivo)

    btn_sim = page.get_by_role("button", name="Sim")
    await expect(btn_sim).to_be_enabled(timeout=config.TIMEOUT_PADRAO)

    if not confirmar:
        log("confirmar_exclusao", "confirmar=False - parando antes do clique irreversivel.", "WARN")
        await screenshot_erro(page, "parada_antes_da_confirmacao")
        return False

    # ACAO IRREVERSIVEL
    await btn_sim.click()
    await expect(page.locator("text=Confirma a exclusão do registro?")).to_be_hidden(timeout=config.TIMEOUT_PADRAO)
    return True


# Etapa 6: valida se o manifesto realmente foi excluido. O ESL aceita o pedido de
# exclusao na hora (modal fecha) mas processa a baixa com atraso - por isso essa
# etapa reconsulta em intervalos em vez de checar uma unica vez.
async def validar_exclusao_efetivada(page, numero, max_tentativas=6, intervalo_s=5):
    campo_numero = page.get_by_role("textbox", name="Número")
    linhas = page.locator("tr.vue-item")

    excluido = False
    for tentativa in range(1, max_tentativas + 1):
        await campo_numero.fill("")
        await campo_numero.fill(numero)
        await campo_numero.press("Enter")
        try:
            await expect(linhas).to_have_count(0, timeout=config.TIMEOUT_PADRAO)
            excluido = True
            break
        except AssertionError:
            log(
                "validar_exclusao_efetivada",
                f"Manifesto {numero} ainda aparece (tentativa {tentativa}/{max_tentativas}), "
                f"aguardando ESL processar a exclusao...",
            )
            await page.wait_for_timeout(intervalo_s * 1000)

    log(
        "validar_exclusao_efetivada",
        f"Manifesto {numero} excluido." if excluido else f"Manifesto {numero} ainda existe.",
    )
    return excluido


# Orquestracao: usada pelo endpoint da API. `confirmar` decide se o clique
# irreversivel em "Sim" acontece de verdade (enviado pelo n8n por requisicao).
async def executar_exclusao(page, numero_manifesto, motivo, confirmar):
    numero = str(numero_manifesto)
    status = "NAO_EXECUTADO"

    try:
        await abrir_manifestos(page)
        await limpar_filtro_data(page)
        await pesquisar_manifesto(page, numero)
        await abrir_menu_e_excluir(page, numero)
        confirmou = await confirmar_exclusao(page, motivo, confirmar)

        if confirmou:
            excluido = await validar_exclusao_efetivada(page, numero)
            status = "SUCESSO" if excluido else "FALHA_VALIDACAO"
        else:
            status = "PARADO_ANTES_DA_CONFIRMACAO"
    except Exception as erro:
        log("executar_exclusao", f"Processo interrompido: {erro}", "ERROR")
        await screenshot_erro(page, "executar_exclusao")
        return {"status": "ERRO", "numeroManifesto": numero, "mensagem": str(erro)}

    log("executar_exclusao", f"Resultado final: {status}")
    return {"status": status, "numeroManifesto": numero, "mensagem": None}
