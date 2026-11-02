#!/usr/bin/env python3
"""Monta o video final: o original, os trechos gerados e o AUDIO ORIGINAL, com um flash branco curto em cada troca.

Roda no SEU computador. Precisa do ffmpeg. No Mac e no Linux, use python3.

A troca fica escondida quando o corte cai com uma mao (ou outra coisa grande) em movimento na frente da camera
e o flash dura uma fracao de segundo. Para achar o ponto, veja os quadros do video (ver references/06-resultado.md).

Cada --parte e um clipe gerado e o segundo do ORIGINAL em que o primeiro quadro dele corresponde (ARQUIVO@SEGUNDO).
Cada --corte e o segundo do original em que entra a parte correspondente. Tem que haver um --corte por --parte.

  python montar.py --original take.mp4 --saida final.mp4 \\
      --parte roupa.mp4@6.25 --parte cenario.mp4@10.02 --corte 6.47 --corte 11.53

  original de 0 a 6,47 s | roupa de 6,47 a 11,53 s | cenario de 11,53 s ate o fim.
  Para VOLTAR ao original no fim, use o proprio original como ultima parte:  --parte take.mp4@0
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

for _f in (sys.stdout, sys.stderr):
    if hasattr(_f, "reconfigure"):
        _f.reconfigure(encoding="utf-8")


def programa(nome):
    p = shutil.which(nome)
    if not p:
        sys.exit(f"Nao achei o '{nome}'. Instale o ffmpeg: Windows: winget install Gyan.FFmpeg | Mac: brew install ffmpeg | Linux: sudo apt install ffmpeg")
    return p


def sondar(arq):
    r = subprocess.run([programa("ffprobe"), "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                        "-of", "json", str(arq)], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        sys.exit(f"O ffprobe nao conseguiu ler {arq}: " + r.stderr.strip()[:300])
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    if not v:
        sys.exit(f"{arq} nao tem video.")
    return {"duracao": float(d["format"]["duration"]), "w": int(v["width"]), "h": int(v["height"]),
            "fps": v["r_frame_rate"], "audio": any(s["codec_type"] == "audio" for s in d["streams"])}


def parte(texto):
    if "@" not in texto:
        raise argparse.ArgumentTypeError("use ARQUIVO@SEGUNDO, por exemplo roupa.mp4@6.25")
    arq, ini = texto.rsplit("@", 1)
    try:
        return arq, float(ini)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{ini}' nao e um numero de segundos")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--original", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--parte", action="append", type=parte, default=[], help="ARQUIVO@SEGUNDO (repita)")
    ap.add_argument("--corte", action="append", type=float, default=[], help="segundo do original (repita)")
    ap.add_argument("--fim", type=float, default=None, help="segundo do original onde termina (padrao: o que o ultimo trecho alcanca)")
    ap.add_argument("--tamanho", default=None, help="LARGURAxALTURA (padrao: o do original)")
    ap.add_argument("--flash-saida", type=float, default=0.07, help="duracao do clarao que fecha o trecho (s)")
    ap.add_argument("--flash-entrada", type=float, default=0.12, help="duracao do clarao que abre o trecho (s)")
    ap.add_argument("--ganho-db", type=float, default=0.0, help="sobe o volume do audio original (com limitador)")
    ap.add_argument("--crf", type=int, default=18)
    o = ap.parse_args()

    if not o.parte or len(o.corte) != len(o.parte):
        sys.exit("Passe um --corte para cada --parte (e pelo menos uma parte).")
    if any(b <= a for a, b in zip(o.corte, o.corte[1:])) or o.corte[0] <= 0:
        sys.exit("Os --corte precisam estar em ordem crescente e maiores que zero.")

    orig = sondar(o.original)
    infos = [sondar(arq) for arq, _ in o.parte]
    if o.tamanho:
        w, h = (int(x) for x in o.tamanho.lower().split("x"))
    else:
        w, h = orig["w"], orig["h"]
    fps = orig["fps"]

    ultimo_alcance = o.parte[-1][1] + infos[-1]["duracao"]
    fim = o.fim if o.fim is not None else min(orig["duracao"], ultimo_alcance)
    if fim <= o.corte[-1] + 0.1:
        sys.exit(f"O video termina em {fim:.2f} s, antes (ou colado) no ultimo corte ({o.corte[-1]:.2f} s).")

    # trechos: (indice da entrada, inicio no arquivo, fim no arquivo, duracao)
    trechos = [(0, 0.0, o.corte[0])]
    limites = o.corte + [fim]
    for i, ((arq, ini), info) in enumerate(zip(o.parte, infos)):
        a, b = limites[i], limites[i + 1]
        if a < ini - 0.05 or b > ini + info["duracao"] + 0.05:
            sys.exit(f"A parte {arq} cobre de {ini:.2f} s a {ini + info['duracao']:.2f} s do original, "
                     f"mas o trecho pedido vai de {a:.2f} s a {b:.2f} s. Ajuste o --corte ou o @SEGUNDO.")
        trechos.append((i + 1, max(a - ini, 0.0), b - ini))

    tam = f"fps={fps},scale={w}:{h}:flags=lanczos,setsar=1"
    f = []
    for k, (idx, a, b) in enumerate(trechos):
        dur = b - a
        cadeia = f"[{idx}:v]trim={a:.4f}:{b:.4f},setpts=PTS-STARTPTS,{tam}"
        if k > 0:
            cadeia += f",fade=t=in:st=0:d={o.flash_entrada}:color=white"
        if k < len(trechos) - 1:
            cadeia += f",fade=t=out:st={max(dur - o.flash_saida, 0):.4f}:d={o.flash_saida}:color=white"
        f.append(cadeia + f"[s{k}]")
    juntos = "".join(f"[s{k}]" for k in range(len(trechos)))
    f.append(f"{juntos}concat=n={len(trechos)}:v=1:a=0,format=yuv420p[v]")
    total = sum(b - a for _, a, b in trechos)
    mapa = ["-map", "[v]"]
    if orig["audio"]:
        ganho = f",volume={o.ganho_db}dB,alimiter=limit=0.89" if o.ganho_db else ""
        f.append(f"[0:a]aresample=48000{ganho},apad,atrim=0:{total:.4f}[a]")
        mapa += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    else:
        print("AVISO: o video original nao tem audio; o final sai sem som.")
        mapa += ["-an"]

    cmd = [programa("ffmpeg"), "-v", "error", "-y", "-i", o.original] + sum((["-i", arq] for arq, _ in o.parte), []) + \
          ["-filter_complex", ";".join(f)] + mapa + ["-c:v", "libx264", "-crf", str(o.crf), "-preset", "medium", "-movflags", "+faststart", o.saida]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit("O ffmpeg falhou: " + r.stderr.strip()[-700:])
    final = sondar(o.saida)
    print(f"Pronto: {o.saida}")
    print(f"  {final['duracao']:.2f} s (esperado {total:.2f} s) | {final['w']}x{final['h']} | audio: {'original' if orig['audio'] else 'sem'}")
    print("  trechos: " + " | ".join(f"{'original' if i == 0 else o.parte[i - 1][0]} {a + (0 if i == 0 else o.parte[i - 1][1]):.2f}-{b + (0 if i == 0 else o.parte[i - 1][1]):.2f}" for i, (_, a, b) in enumerate(trechos)))


if __name__ == "__main__":
    main()
