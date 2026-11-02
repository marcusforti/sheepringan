#!/usr/bin/env python3
"""Trocar a pessoa (ou o personagem) do video pelo workflow "relay" (h3-relay + LoRA de troca de personagem).

Roda DENTRO da maquina alugada, com o perfil "relay" instalado. E o rodar_relay.py testado em 01/11/2026,
com parametros no lugar de argumentos soltos e variaveis de ambiente.

  python relay.py --video fonte.mp4 --ref pessoa.png --rotulo troca1 \\
      --prompt "Replace the selected person in <Video 1> with the character in <Picture 1>. Keep his exact face and identity. Follow the source performance's pose, gaze, expression and mouth movement. Preserve the scene."

O workflow e o H3-Character-Swap.api.json que vem dentro do repositorio h3-relay (GPL-3.0); ele nao
e copiado para este projeto. Videos de 12 s estouraram a memoria da placa duas vezes: comece com ate ~6 s.
Resultado: /root/ComfyUI/output/relay/<rotulo>*.mp4
"""
import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comfy_api import conferir_ligacoes, enviar, esperar  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--video", required=True)
ap.add_argument("--ref", required=True, help="imagem de referencia (pode ser uma folha com 2 a 3 fotos reais do rosto)")
ap.add_argument("--rotulo", default="relay")
ap.add_argument("--prompt", required=True, help="descricao do que trocar, em ingles")
ap.add_argument("--resolucao", default="768")
ap.add_argument("--seed", type=int, default=904239)
ap.add_argument("--sam", default="person", help="o que o SAM acha para trocar")
ap.add_argument("--mem", type=float, default=None, help="activation_memory_gib (reduza se faltar memoria de video)")
ap.add_argument("--expandir", type=int, default=None, help="expansion_px da mascara de edicao (padrao do workflow: 64)")
ap.add_argument("--sem-adaptador", action="store_true", help="nao usa a LoRA de troca de personagem")
ap.add_argument("--workflow", default="/root/ComfyUI/custom_nodes/h3-relay/example_workflows/toolkit/H3-Character-Swap.api.json")
ap.add_argument("--comfy", default="http://127.0.0.1:8188")
ap.add_argument("--entrada", default="/root/ComfyUI/input")
ap.add_argument("--espera-max", type=int, default=2700)
o = ap.parse_args()

g = json.load(open(o.workflow, encoding="utf-8"))
for p in (o.video, o.ref):
    shutil.copy(p, o.entrada)

g["source"]["inputs"]["file"] = os.path.basename(o.video)
g["reference"]["inputs"]["image"] = os.path.basename(o.ref)
g["prepare"]["inputs"]["resolution"] = o.resolucao
g["subject"]["inputs"]["text"] = o.sam
g["plan"]["inputs"]["seed"] = o.seed
g["reference_conditioning"]["inputs"]["prompt"] = o.prompt
g["save"]["inputs"]["filename_prefix"] = "relay/" + o.rotulo
if o.mem is not None:
    g["sampling_memory"]["inputs"]["activation_memory_gib"] = o.mem
if o.expandir is not None:
    g["expand_mask"]["inputs"]["expansion_px"] = o.expandir
if o.sem_adaptador:
    g["sampling_memory"]["inputs"]["model"] = ["turbo", 0]
    g["schedule"]["inputs"]["model"] = ["turbo", 0]
conferir_ligacoes(g)

pid = enviar(g, o.comfy)
sys.exit(esperar(pid, o.comfy, o.espera_max))
