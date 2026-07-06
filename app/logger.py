from datetime import datetime, timezone


def log(etapa, mensagem, nivel="INFO"):
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"[{timestamp}] [{nivel}] [{etapa}] {mensagem}", flush=True)
