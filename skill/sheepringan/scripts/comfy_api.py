"""Pecas comuns dos scripts que rodam DENTRO da maquina alugada: mandar o trabalho ao ComfyUI e esperar.

So biblioteca padrao. O ComfyUI escuta so em 127.0.0.1:8188 dentro da maquina.
"""
import json
import sys
import time
import urllib.error
import urllib.request


def liga(v):
    return isinstance(v, list) and len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], int)


def conferir_ligacoes(g):
    """Falha cedo se alguma ligacao aponta para um no que foi apagado."""
    for k, n in g.items():
        for c, v in n["inputs"].items():
            if liga(v) and v[0] not in g:
                raise SystemExit(f"ligacao quebrada {k}.{c} -> {v[0]}")


def no_por_titulo(g, titulo):
    for k, n in g.items():
        if n.get("_meta", {}).get("title") == titulo:
            return k
    raise SystemExit(
        f"sem no com o titulo: {titulo!r}. O workflow do Openjutsu mudou; "
        "use as versoes testadas (instalar_maquina.sh sem --ultimas)."
    )


def enviar(g, comfy, client_id="sheepringan"):
    corpo = json.dumps({"prompt": g, "client_id": client_id}).encode()
    pedido = urllib.request.Request(comfy + "/prompt", corpo, {"Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(pedido, timeout=60))
    except urllib.error.HTTPError as e:
        print("ERRO_PROMPT", e.read().decode(errors="replace")[:3000], flush=True)
        sys.exit(1)
    except urllib.error.URLError as e:
        print("ERRO_COMFY_FORA", e, "- o ComfyUI esta ligado? Rode: bash instalar_maquina.sh --so-comfy", flush=True)
        sys.exit(2)
    pid = r["prompt_id"]
    print("ENVIADO", pid, time.strftime("%H:%M:%S"), flush=True)
    return pid


def esperar(pid, comfy, espera_max=2400, intervalo=15):
    """Espera o trabalho terminar. Imprime STATUS, ERRO_EXEC, RUN e SAIDAS."""
    t0 = time.time()
    fora = 0
    while True:
        time.sleep(intervalo)
        if time.time() - t0 > espera_max:
            print("ERRO_TEMPO passou de", espera_max, "s sem terminar", flush=True)
            sys.exit(3)
        try:
            h = json.load(urllib.request.urlopen(comfy + "/history/" + pid, timeout=60))
            fora = 0
        except (urllib.error.URLError, OSError) as e:
            fora += 1
            if fora >= 4:
                print("ERRO_COMFY_FORA parou de responder:", e, flush=True)
                sys.exit(2)
            continue
        if pid not in h:
            continue
        s = h[pid].get("status", {})
        print("STATUS", s.get("status_str"), s.get("completed"), round(time.time() - t0), "s", flush=True)
        erro = False
        for m in s.get("messages", []):
            if m[0] == "execution_error":
                erro = True
                print("ERRO_EXEC", json.dumps(m[1])[:2500], flush=True)
        saidas = h[pid].get("outputs", {})
        for no in saidas.values():
            for cena in no.get("h3_chain_active_scene", []):
                print("RUN", cena.get("run_name"), flush=True)
        print("SAIDAS", json.dumps(saidas)[:1500], flush=True)
        return 1 if erro else 0
