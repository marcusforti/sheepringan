"""ssh e scp de mentira para os testes: o "computador remoto" e uma pasta temporaria deste computador.

Uso (montado por remoto.py):  ssh_falso.py ssh ... destino "comando"   |   ssh_falso.py scp ... origem... destino
O comando remoto roda de verdade, com o bash local, e a raiz remota (SHEEPRINGAN_RAIZ_REMOTA) aponta para a pasta temporaria.
"""
import shutil
import subprocess
import sys
from pathlib import Path

modo, resto = sys.argv[1], sys.argv[2:]

if modo == "ssh":
    comando = resto[-1]
    r = subprocess.run([shutil.which("bash"), "-c", comando], capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    sys.exit(r.returncode)


def remoto(p):
    return "@" in p and ":" in p.split("@", 1)[1]


def caminho(p):
    return Path(p.split("@", 1)[1].split(":", 1)[1])


# scp: tira os pares de opcao (-i x, -P n, -o y) e sobram origens... e destino
palavras = []
i = 0
while i < len(resto):
    if resto[i] in ("-i", "-P", "-p", "-o"):
        i += 2
        continue
    palavras.append(resto[i])
    i += 1
*origens, destino = palavras

if remoto(destino):  # envio
    pasta = caminho(destino)
    pasta.mkdir(parents=True, exist_ok=True)
    for o in origens:
        shutil.copy(o, pasta / Path(o).name)
else:  # download
    src = caminho(origens[0])
    if not src.exists():
        sys.stderr.write(f"scp: {src}: No such file or directory\n")
        sys.exit(1)
    shutil.copy(src, Path(destino) / src.name if Path(destino).is_dir() else destino)
