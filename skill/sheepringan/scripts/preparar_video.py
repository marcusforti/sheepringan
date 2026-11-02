#!/usr/bin/env python3
"""Prepara o video do celular para o Openjutsu.

Roda no SEU computador. Precisa do ffmpeg e do ffprobe (Windows: winget install Gyan.FFmpeg | Mac: brew install ffmpeg).
No Mac e no Linux, use python3.

O que o Openjutsu exige, e este script faz:
  1. 24 quadros por segundo, constantes (video de celular costuma ser 30 e variavel).
  2. Um numero exato de quadros: 17 x k + 5 (22, 39, 56, 73, 90, 107, 124, 141, 158...). Assim o trecho vira UM clipe so.
  3. Audio do mesmo tamanho do video ou maior. Se o audio for menor, a montagem final do Openjutsu falha
     (H3 Source Timeline audio window 0:158 exceeds 0:157). Se o video nao tem audio, entra um silencio.
  4. Lado menor de ate 720 px (o Openjutsu trabalha em ~736 px; mais que isso so gasta envio).

  python preparar_video.py take.mp4 --inicio 6.25 --quadros 158
  python preparar_video.py take.mp4 --duracao 3          (usa o maior numero valido de quadros que cabe)
  python preparar_video.py take.mp4                      (do comeco, ate 158 quadros ou o que o video tiver)

No fim ele imprime o valor de --clip para usar no objeto.py.
Videos com legenda queimada na imagem dao resultado ruim: tire a legenda antes e ponha depois.
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

FPS = 24
MAX_PADRAO = 158  # 6,6 s: o maior trecho que testamos no modo Object


def valido(n):
    return n >= 5 and (n - 5) % 17 == 0


def validos_ate(n):
    return [17 * k + 5 for k in range(0, 200) if 17 * k + 5 <= n]


def programa(nome):
    p = shutil.which(nome)
    if not p:
        sys.exit(f"Nao achei o '{nome}'. Instale o ffmpeg: Windows: winget install Gyan.FFmpeg | Mac: brew install ffmpeg | Linux: sudo apt install ffmpeg")
    return p


def sondar(arq):
    r = subprocess.run([programa("ffprobe"), "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate,duration,nb_frames",
                        "-of", "json", str(arq)], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        sys.exit("O ffprobe nao conseguiu ler o video: " + r.stderr.strip()[:300])
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    au = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    if not v:
        sys.exit("Esse arquivo nao tem video.")
    return {
        "duracao": float(d["format"].get("duration") or v.get("duration") or 0),
        "largura": int(v["width"]), "altura": int(v["height"]),
        "audio": au is not None,
        "dur_video": float(v.get("duration") or d["format"].get("duration") or 0),
        "dur_audio": float(au.get("duration") or 0) if au else 0.0,
        "quadros": int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else None,
    }


def contar_quadros(arq):
    r = subprocess.run([programa("ffprobe"), "-v", "error", "-count_frames", "-select_streams", "v:0",
                        "-show_entries", "stream=nb_read_frames,r_frame_rate", "-of", "json", str(arq)],
                       capture_output=True, text=True, encoding="utf-8")
    s = json.loads(r.stdout)["streams"][0]
    return int(s["nb_read_frames"]), s["r_frame_rate"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada")
    ap.add_argument("-o", "--saida", default=None)
    ap.add_argument("--inicio", type=float, default=0.0, help="segundo do video onde o trecho comeca")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--quadros", type=int, help="quantidade exata de quadros (17k+5)")
    g.add_argument("--duracao", type=float, help="segundos desejados; usa o maior valido que cabe")
    ap.add_argument("--max-quadros", type=int, default=MAX_PADRAO, help=f"teto quando nada e pedido (padrao {MAX_PADRAO})")
    ap.add_argument("--lado-menor", type=int, default=720)
    o = ap.parse_args()

    entrada = Path(o.entrada)
    if not entrada.exists():
        sys.exit(f"Nao achei o video: {entrada}")
    info = sondar(entrada)
    disponivel = int((info["duracao"] - o.inicio) * FPS + 0.05)  # tolera o arredondamento da duracao
    if disponivel < 5:
        sys.exit(f"Depois de {o.inicio:g} s sobra so {max(disponivel, 0)} quadro(s). O minimo e 5.")

    if o.quadros is not None:
        n = o.quadros
        if not valido(n):
            sys.exit(f"{n} quadros nao serve. Use 17 x k + 5: {', '.join(map(str, validos_ate(200)[:12]))}...")
        if n > disponivel:
            sys.exit(f"O video so tem {disponivel} quadros a partir de {o.inicio:g} s. Maior valido: {validos_ate(disponivel)[-1]}.")
    else:
        teto = int(o.duracao * FPS + 0.05) if o.duracao else o.max_quadros
        n = validos_ate(min(disponivel, teto))[-1]

    saida = Path(o.saida) if o.saida else entrada.with_name(entrada.stem + "_prep.mp4")
    total = n / FPS + 0.5  # o audio vai um pouco alem do video, de proposito
    menor = o.lado_menor
    escala = f"scale=w='if(gt(iw,ih),-2,min({menor},iw))':h='if(gt(iw,ih),min({menor},ih),-2)':flags=lanczos"
    cmd = [programa("ffmpeg"), "-v", "error", "-y", "-ss", f"{o.inicio:.3f}", "-i", str(entrada)]
    if info["audio"]:
        mapa = ["-map", "0:v:0", "-map", "0:a:0"]
        af = "aresample=48000,apad"
    else:
        cmd += ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        mapa = ["-map", "0:v:0", "-map", "1:a:0"]
        af = "aresample=48000,apad"
        print("AVISO: o video nao tem audio. Entrou um silencio; sem som, a boca da pessoa nao tem o que acompanhar.")
    # O corte de quadros vai no filtro (trim), nao em -frames:v: com -frames:v o ffmpeg encerra o arquivo inteiro
    # quando o video acaba e corta o audio junto, deixando-o menor que o video.
    cmd += mapa + ["-vf", f"fps={FPS},{escala},setsar=1,trim=end_frame={n},setpts=PTS-STARTPTS", "-af", af, "-t", f"{total:.3f}",
                   "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(saida)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit("O ffmpeg falhou: " + r.stderr.strip()[-600:])

    # confere o resultado de verdade
    quadros, taxa = contar_quadros(saida)
    s = sondar(saida)
    ok = quadros == n and taxa == f"{FPS}/1" and s["audio"] and s["dur_audio"] + 1e-3 >= n / FPS
    # Ate 158 quadros: --clip do tamanho do trecho (um clipe so). Mais que isso: --clip 6, e o Openjutsu emenda
    # varios clipes (testado com 226 e 260 quadros).
    clip = round(n / FPS + 0.02, 3) if n <= MAX_PADRAO else 6
    print(f"Pronto: {saida}")
    print(f"  quadros: {quadros} (pedido {n}) | taxa: {taxa} | video: {n / FPS:.3f} s | audio: {s['dur_audio']:.3f} s | {s['largura']}x{s['altura']}")
    print(f"  Use no objeto.py:  --clip {clip}")
    if n > MAX_PADRAO:
        print(f"  Trecho comprido ({n} quadros): vira varios clipes de ate 6 s. Testado com 226 e 260 quadros, so no modo adicionar.")
    print(json.dumps({"arquivo": str(saida), "quadros": quadros, "fps": FPS, "segundos": round(n / FPS, 3), "clip": clip, "ok": ok}))
    if not ok:
        print("ATENCAO: a conferencia falhou (quadros, taxa ou audio). Nao mande esse arquivo para a GPU.")
        sys.exit(1)


if __name__ == "__main__":
    main()
