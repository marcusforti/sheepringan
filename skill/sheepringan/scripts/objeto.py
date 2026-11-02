#!/usr/bin/env python3
"""Roda o modo Object do Openjutsu pela API do ComfyUI, com os mesmos ajustes de lib/object.ts.

Exemplos:
  python objeto.py --modo change --video roupa.mp4 --foto ref.png --rotulo take --alvo top --sam hoodie
      --para "a red denim jacket" --desc "A red denim jacket with metal buttons." --margem 20 --clip 6.6
  python objeto.py --modo background --video fundo.mp4 --foto ref.png --rotulo take --alvo person --sam person
      --para "a dark office" --desc "A dark office with red neon." --margem 10 --clip 2.5
  python objeto.py --modo add --video mesa.mp4 --foto ref.png --rotulo take --alvo "on the wooden table"
      --para "a tiny cartoon sheep" --desc "A tiny cartoon sheep." --margem 2 --clip 3.05
      --caixa 0.28,0.5,0.44,0.34 --acao "she waves at the camera"
--clip em segundos: int(clip*24) e arredondado para baixo na grade 17k+5 quadros.
"""
import argparse, json, os, shutil, sys, time, urllib.error, urllib.request

ap = argparse.ArgumentParser()
for a, d in (("--modo", None), ("--video", None), ("--foto", ""), ("--rotulo", "edit"), ("--alvo", None), ("--sam", ""), ("--para", ""), ("--desc", ""),
             ("--caixa", ""), ("--acao", ""), ("--workflow", "/root/openjutsu/workflows/object.api.json"), ("--comfy", "http://127.0.0.1:8188"), ("--entrada", "/root/ComfyUI/input")):
    ap.add_argument(a, default=d, required=d is None)
ap.add_argument("--margem", type=int, default=20)
ap.add_argument("--clip", type=float, default=6.0)
ap.add_argument("--seed", type=int, default=904239)
ap.add_argument("--resolucao", default="736p")
ap.add_argument("--todos", action="store_true", help="mantem todos os objetos que o SAM achar; use com varios alvos, como camiseta e bracos")
ap.add_argument("--sem-contorno", action="store_true", help="change: nao manda a forma cinza (troca a silhueta, perde guia de maos e bracos)")
o = ap.parse_args()

g = json.load(open(o.workflow, encoding="utf-8"))

def nid(t):
    for k, n in g.items():
        if n.get("_meta", {}).get("title") == t:
            return k
    raise SystemExit("sem no: " + t)

tem_foto = bool(o.foto) and o.modo != "remove"
shutil.copy(o.video, o.entrada)
if tem_foto:
    shutil.copy(o.foto, o.entrada)

plan = g[nid("Object Swap Plan (what to change)")]["inputs"]
ref = g[nid("Reference Conditioning")]["inputs"]
grow = g[nid("Grow mask")]["inputs"]
grey = g[nid("Turn it grey (shape and movement only)")]["inputs"]

if tem_foto and o.desc:
    d = g[nid("Describe picture 1")]["inputs"]
    d["prompt"] = "Output exactly this sentence and nothing else: " + o.desc
    d["max_length"] = 160
if not tem_foto:
    for t in ("Picture 1", "Shrink for the describer", "Describe picture 1"):
        del g[nid(t)]
    plan.pop("picture_1", None)
    plan.pop("picture_1_text", None)
    ref.pop("ref_images.ref_image_0", None)
if o.modo in ("remove", "add") or (o.modo == "change" and o.sem_contorno):
    ref.pop("ref_videos.ref_video_0", None)
    ref.pop("ref_video_audios.ref_video_audio_0", None)
if o.modo == "background":
    grow["flip_input"] = True
    grey["mask"] = [nid("Grow mask"), 0]
    grey["size"] = [nid("Grow mask"), 0]
grow["expand"] = o.margem
if o.modo != "add":
    for t in ("Tracked area", "Tracked area, tight (for the grey shape)"):
        g[nid(t)]["inputs"]["max_people"] = 0 if o.todos else 1
    g[nid("SAM: what to change")]["inputs"]["text"] = o.sam or o.alvo
plan.update(mode=o.modo, target=o.alvo, change_to=o.para, keep_outline=not o.sem_contorno, seed=o.seed, clip_seconds=o.clip, resolution=o.resolucao)

if o.modo == "add":
    x, y, w, h = [float(v) for v in o.caixa.split(",")]
    caixa = json.dumps([{"frame": 0, "x": x, "y": y, "width": w, "height": h}])
    plan.update(placement=caixa, keep_outline=False, action=o.acao)
    g["object_placement"] = {"class_type": "H3ObjectPlacementMask",
                             "inputs": {"images": [nid("Source clip (frames + audio)"), 0], "start_frame": [nid("Clip start frame"), 1], "placement": caixa},
                             "_meta": {"title": "Object placement area"}}
    drop = [nid(t) for t in ("SAM frames for this clip", "Tracked area", "Tracked area, tight (for the grey shape)", "Turn it grey (shape and movement only)",
                             "SAM 3.1", "SAM: what to change", "SAM video (1008 px, SAM's own size)", "SAM 3.1 track it")]
    grow["mask"] = ["object_placement", 0]
    for k in drop:
        del g[k]

g[nid("Source video")]["inputs"]["video"] = os.path.basename(o.video)
if tem_foto:
    g[nid("Picture 1")]["inputs"]["image"] = os.path.basename(o.foto)
g[nid("Final Video")]["inputs"]["filename"] = o.rotulo

liga = lambda v: isinstance(v, list) and len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], int)
for k, n in g.items():
    for c, v in n["inputs"].items():
        if liga(v) and v[0] not in g:
            raise SystemExit(f"ligacao quebrada {k}.{c} -> {v[0]}")

b = json.dumps({"prompt": g, "client_id": "sheepringan"}).encode()
try:
    r = json.load(urllib.request.urlopen(urllib.request.Request(o.comfy + "/prompt", b, {"Content-Type": "application/json"}), timeout=60))
except urllib.error.HTTPError as e:
    print("ERRO_PROMPT", e.read().decode()[:3000])
    sys.exit(1)
pid = r["prompt_id"]
print("ENVIADO", pid, time.strftime("%H:%M:%S"), flush=True)
t0 = time.time()
while True:
    time.sleep(15)
    h = json.load(urllib.request.urlopen(o.comfy + "/history/" + pid, timeout=60))
    if pid in h:
        s = h[pid].get("status", {})
        print("STATUS", s.get("status_str"), s.get("completed"), round(time.time() - t0), "s", flush=True)
        for m in s.get("messages", []):
            if m[0] == "execution_error":
                print("ERRO_EXEC", json.dumps(m[1])[:2500], flush=True)
        for no in h[pid].get("outputs", {}).values():
            for cena in no.get("h3_chain_active_scene", []):
                print("RUN", cena.get("run_name"), flush=True)
        break
