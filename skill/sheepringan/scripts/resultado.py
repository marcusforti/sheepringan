#!/usr/bin/env python3
"""Traz o resultado da maquina alugada para o seu computador, inclusive quando a montagem final do Openjutsu falha.

Roda no SEU computador. No Mac e no Linux, use python3.

  python resultado.py ROTULO [--saida PASTA] [--run edit_abc123]

ROTULO e o --rotulo que voce usou no objeto.py (ou trocar_pessoa.py, relay.py).

Procura primeiro o video pronto, com audio:
  /root/ComfyUI/output/h3_oneclick_edit/ROTULO*.mp4   (objeto.py)
  /root/ComfyUI/output/h3_oneclick_swap/ROTULO*.mp4   (trocar_pessoa.py)
  /root/ComfyUI/output/relay/ROTULO*.mp4              (relay.py)
Se nao achar, a montagem final falhou (quase sempre porque o audio era menor que o video). Mas o trecho
gerado ja existe, SEM audio, em:
  /root/ComfyUI/output/h3_chains/<run>/generation/clips/
O objeto.py imprime a linha "RUN <nome>" com esse nome; passe em --run. Sem --run, pega o mais novo.
O montar.py usa o audio do video original, entao um clipe sem audio serve.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import remoto  # noqa: E402

SAIDA = remoto.RAIZ + "/ComfyUI/output"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rotulo")
    ap.add_argument("--saida", default=".")
    ap.add_argument("--run", default=None, help="nome da pasta em h3_chains (linha RUN do objeto.py)")
    o = ap.parse_args()
    if not o.rotulo or not all(c.isalnum() or c in "_-." for c in o.rotulo):
        sys.exit("O rotulo so pode ter letras, numeros, _ - e .")
    if o.run and not all(c.isalnum() or c in "_-" for c in o.run):
        sys.exit("O nome do --run so pode ter letras, numeros, _ e -")

    e = remoto.estado()
    clipes = f"{SAIDA}/h3_chains/{o.run}/generation/clips" if o.run else f"{SAIDA}/h3_chains/*/generation/clips"
    script = (
        f"for d in h3_oneclick_edit h3_oneclick_swap relay; do\n"
        f"  f=$(ls -t {SAIDA}/$d/{o.rotulo}*.mp4 2>/dev/null | head -1)\n"
        f"  if [ -n \"$f\" ]; then echo \"PRONTO $f\"; exit 0; fi\n"
        f"done\n"
        f"f=$(ls -t {clipes}/*.mp4 2>/dev/null | head -1)\n"
        f"if [ -n \"$f\" ]; then echo \"SEM_AUDIO $f\"; exit 0; fi\n"
        f"echo NADA\n"
    )
    rc, out, err = remoto.executar(e, script, tempo=90)
    linha = next((x for x in out.splitlines() if x.startswith(("PRONTO ", "SEM_AUDIO ", "NADA"))), "NADA")
    if linha == "NADA":
        print("Nao achei nenhum resultado para esse rotulo. O trabalho terminou? Veja o log com:  python remoto.py log NOME")
        return 1
    tipo, caminho = linha.split(" ", 1)
    pasta = Path(o.saida).resolve()
    pasta.mkdir(parents=True, exist_ok=True)
    nome_remoto = Path(caminho).name
    cmd = remoto.achar("scp") + remoto.opcoes(e, "-P") + [f"{remoto.destino(e)}:{caminho}", "."]
    r = subprocess.run(cmd, cwd=str(pasta), text=True, capture_output=True)
    if r.returncode != 0:
        sys.exit("Falhou o download: " + (r.stderr or r.stdout).strip()[:400])
    baixado = pasta / nome_remoto
    if tipo == "SEM_AUDIO":
        novo = pasta / f"{o.rotulo}_clipe_sem_audio.mp4"
        baixado.replace(novo)
        baixado = novo
    print(f"Baixado: {baixado}")
    if tipo == "SEM_AUDIO":
        print("Este clipe veio SEM audio (a montagem final falhou). Sem problema: o montar.py usa o audio do video original.")
    print(json.dumps({"arquivo": str(baixado), "tipo": tipo.lower(), "origem": caminho}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
