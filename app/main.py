from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import browser_manager, config
from .excluir_manifesto import executar_exclusao
from .logger import log

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


# Endpoint chamado pelo n8n. Body esperado: { numeroManifesto, motivo, confirmar }
# confirmar=false (ou ausente) so valida o fluxo ate a tela de confirmacao e para.
# confirmar=true executa o clique irreversivel em "Sim".
@app.post("/excluir-manifesto")
async def excluir_manifesto_endpoint(request: Request):
    body = await request.json()
    numero_manifesto = body.get("numeroManifesto")
    motivo = body.get("motivo")
    confirmar = body.get("confirmar") is True

    if not numero_manifesto:
        return JSONResponse(status_code=400, content={"erro": "numeroManifesto e obrigatorio."})
    if not motivo or len(str(motivo).strip()) < 15:
        return JSONResponse(
            status_code=400, content={"erro": "motivo e obrigatorio e deve ter no minimo 15 caracteres."}
        )

    try:
        resultado = await browser_manager.executar(
            lambda page: executar_exclusao(page, numero_manifesto, str(motivo), confirmar)
        )
        codigo = 500 if resultado["status"] == "ERRO" else 200
        return JSONResponse(status_code=codigo, content=resultado)
    except Exception as erro:
        log("server", f"Erro inesperado: {erro}", "ERROR")
        return JSONResponse(status_code=500, content={"status": "ERRO", "mensagem": str(erro)})


@app.on_event("shutdown")
async def desligar():
    log("server", "Encerrando...")
    await browser_manager.encerrar()
