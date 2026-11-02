#!/usr/bin/env python3
"""Trocar a pessoa do video por outra (workflow "simple" do Openjutsu), pela API do ComfyUI.

Roda DENTRO da maquina alugada. E o rodar_swap.py testado em 01/11/2026, com parametros em vez de
numeros de no: mesmos ajustes de lib/simple.ts do Openjutsu (sem a correcao de chapeu, com lip-sync,
margem normal). Os nos sao achados pelo titulo.

  python trocar_pessoa.py --video fonte.mp4 --foto pessoa.png --rotulo troca1
  python trocar_pessoa.py --video fonte.mp4 --foto pessoa.png --rotulo troca1 --papel "the singer" --resolucao 736p

Quem entra e a pessoa da foto; quem sai e a pessoa MAIOR do quadro. As outras ficam como estao.
Resultado: /root/ComfyUI/output/h3_oneclick_swap/<rotulo>*.mp4
"""
import argparse
import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comfy_api import conferir_ligacoes, enviar, esperar, liga, no_por_titulo  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--video", required=True)
ap.add_argument("--foto", required=True, help="foto da pessoa que vai entrar (de preferencia um quadro real, nao imagem de IA)")
ap.add_argument("--rotulo", default="troca")
ap.add_argument("--resolucao", default="736p")
ap.add_argument("--papel", default="", help='quem sai, pelo papel e nao pela roupa. Ex.: "the singer". Vazio: o descritor nomeia')
ap.add_argument("--clip", type=float, default=6, help="segundos por clipe (padrao 6)")
ap.add_argument("--seed", type=int, default=None, help="padrao: sorteado pelo relogio")
ap.add_argument("--sam", default="person", help='o que o SAM acha para trocar (padrao "person")')
ap.add_argument("--desc", default="", help="descricao fixa da pessoa da foto, em ingles (vira uma frase so)")
ap.add_argument("--workflow", default="/root/openjutsu/workflows/simple.api.json")
ap.add_argument("--comfy", default="http://127.0.0.1:8188")
ap.add_argument("--entrada", default="/root/ComfyUI/input")
ap.add_argument("--espera-max", type=int, default=2400)
o = ap.parse_args()

g = json.load(open(o.workflow, encoding="utf-8"))
for p in (o.video, o.foto):
    shutil.copy(p, o.entrada)

nid = lambda t: no_por_titulo(g, t)  # noqa: E731
# sem a correcao de chapeu: a mascara da pessoa vai direto para o "Grow mask"
for t in ("SAM: hats", "SAM 3.1 track hats", "All hats", "Hat search area (person + 60 px)", "Only the main person's hat", "People + hats"):
    del g[nid(t)]
grow = g[nid("Grow mask (~4% of the frame)")]["inputs"]
grow["mask"] = [nid("Main person (+ headroom)"), 0]
grow["expand"] = 40
g[nid("SAM: what to replace")]["inputs"]["text"] = o.sam

# com lip-sync: tira os nos de "sem lip-sync" e liga o que passava por eles direto
MUDO = re.compile(r"^Mute the (clip|reference) audio H3 hears$")
SEM_LIP = re.compile(r"^(No lip-sync in the prompt|SAM: faces|SAM 3\.1 track faces|Faces \(shown on the mannequins?\))$")
passa = {}
for i, n in g.items():
    t = n.get("_meta", {}).get("title", "")
    if MUDO.match(t):
        passa[i] = n["inputs"]["audio"]
    elif SEM_LIP.match(t):
        passa[i] = None
for i in passa:
    del g[i]
for i, n in g.items():
    for k, v in list(n["inputs"].items()):
        if liga(v) and v[0] in passa:
            if passa[v[0]]:
                n["inputs"][k] = passa[v[0]]
            elif k in ("no_lip_sync", "faces", "face_size"):
                del n["inputs"][k]
            else:
                raise SystemExit(f"ligacao sem destino {i}.{k}")

g[nid("Swap Plan (roles, seed, size)")]["inputs"].update(
    resolution=o.resolucao,
    seed=o.seed if o.seed is not None else int(time.time()) % 100000,
    clip_seconds=o.clip,
    roles=o.papel,
)
g[nid("Source video (people get replaced)")]["inputs"]["video"] = os.path.basename(o.video)
g[nid("Picture 1")]["inputs"]["image"] = os.path.basename(o.foto)
g[nid("Final Video")]["inputs"]["filename"] = o.rotulo
if o.desc:
    g[nid("Describe picture 1")]["inputs"]["prompt"] = "Output exactly this sentence and nothing else: " + o.desc
    grow["expand"] = 60
conferir_ligacoes(g)

pid = enviar(g, o.comfy)
sys.exit(esperar(pid, o.comfy, o.espera_max))
