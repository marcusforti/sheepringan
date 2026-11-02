#!/usr/bin/env python3
"""Fala com a maquina alugada por SSH, sem dor de cabeca de aspas e caminhos (funciona no Windows, Mac e Linux).

Roda no SEU computador. Usa o ssh e o scp que ja vem no Windows 10/11, no Mac e no Linux.
O endereco da maquina vem de ~/.sheepringan/maquina.json, gravado por `vast.py alugar`.
No Mac e no Linux, use python3.

  python remoto.py testar                          confere que a maquina responde
  python remoto.py subir                           manda os scripts da maquina (objeto.py etc.) para /root/sheepringan/
  python remoto.py enviar ARQUIVO [DESTINO]        manda um arquivo (padrao: /root/trabalho/)
  python remoto.py baixar ARQUIVO_REMOTO [PASTA]   traz um arquivo (padrao: pasta atual)
  python remoto.py rodar "COMANDO"                 roda um comando curto e mostra o resultado
  python remoto.py fundo NOME "COMANDO"            roda um comando longo sem prender o terminal
  Em COMANDO, "@arquivo.sh" usa o texto de um arquivo seu: evita brigar com aspas, principalmente no Windows.
  python remoto.py log NOME [--linhas 30]          mostra o fim do que o comando longo escreveu
  python remoto.py espera NOME [--max 8]           espera (ate N minutos) o comando longo terminar
"""
import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

for _f in (sys.stdout, sys.stderr):
    if hasattr(_f, "reconfigure"):
        _f.reconfigure(encoding="utf-8", errors="replace")

CASA = Path(os.environ.get("SHEEPRINGAN_HOME") or (Path.home() / ".sheepringan"))
AQUI = Path(__file__).resolve().parent
ARQUIVOS_DA_MAQUINA = ["objeto.py", "trocar_pessoa.py", "relay.py", "comfy_api.py", "instalar_maquina.sh"]
ATIVAR = "[ -f /venv/main/bin/activate ] && source /venv/main/bin/activate; "
RAIZ = os.environ.get("SHEEPRINGAN_RAIZ_REMOTA", "/root")  # so os testes mudam isto
PASTA_REMOTA = RAIZ + "/sheepringan"
TRABALHO = RAIZ + "/trabalho"


def estado():
    p = CASA / "maquina.json"
    if not p.exists():
        sys.exit("Nao ha maquina registrada. Alugue uma antes: python vast.py ofertas / alugar")
    e = json.loads(p.read_text(encoding="utf-8"))
    if not e.get("host") or not e.get("port"):
        sys.exit("A maquina ainda nao tem endereco SSH. Rode `python vast.py status` e espere ficar 'running'.")
    return e


def achar(nome):
    """Devolve o comando como lista. SHEEPRINGAN_SSH / SHEEPRINGAN_SCP trocam o programa (usado nos testes)."""
    env = os.environ.get("SHEEPRINGAN_" + nome.upper())
    if env:
        return json.loads(env) if env.lstrip().startswith("[") else [env]
    achado = shutil.which(nome)
    if not achado:
        sys.exit(f"Nao achei o programa '{nome}' neste computador. No Windows 10/11 ative o 'Cliente OpenSSH' em "
                 "Configuracoes > Aplicativos > Recursos opcionais. No Mac e no Linux ele ja vem.")
    return [achado]


def arquivo_de_hosts():
    """Caminho do known_hosts proprio. Barras normais e aspas se tiver espaco: o ssh trata espaco como lista de arquivos."""
    p = (CASA / "known_hosts").as_posix()
    return '"' + p + '"' if " " in p else p


def opcoes(e, porta_flag):
    CASA.mkdir(parents=True, exist_ok=True)
    return [
        "-i", os.path.expanduser(e.get("chave") or "~/.ssh/vast_ed25519"), porta_flag, str(e["port"]),
        "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new",
        "-o", "UserKnownHostsFile=" + arquivo_de_hosts(),
        "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=6",
        "-o", "ConnectTimeout=25", "-o", "LogLevel=ERROR",
    ]


def destino(e):
    return f"{e.get('usuario') or 'root'}@{e['host']}"


def ssh_args(e, comando):
    return achar("ssh") + opcoes(e, "-p") + [destino(e), comando]


def embrulhar(script):
    """Manda o texto do comando em base64, para nao ter problema de aspas em nenhum sistema."""
    b = base64.b64encode(script.encode("utf-8")).decode("ascii")
    return f"mkdir -p {TRABALHO}; echo {b} | base64 -d > {TRABALHO}/.cmd.$$.sh; bash -l {TRABALHO}/.cmd.$$.sh; rc=$?; rm -f {TRABALHO}/.cmd.$$.sh; exit $rc"


def executar(e, script, tempo=None):
    try:
        r = subprocess.run(ssh_args(e, embrulhar(ATIVAR + script)), text=True, encoding="utf-8", errors="replace",
                           capture_output=True, timeout=tempo)
    except subprocess.TimeoutExpired:
        return 124, "", f"Passaram {tempo} s sem resposta. Para comandos longos use `fundo` e `espera`."
    return r.returncode, r.stdout, r.stderr


def texto_do_comando(c):
    if c.startswith("@"):
        arq = Path(c[1:])
        if not arq.is_file():
            sys.exit(f"Nao achei o arquivo do comando: {arq}")
        return arq.read_text(encoding="utf-8").replace("\r\n", "\n")
    return c


def cmd_testar(a):
    e = estado()
    rc, out, err = executar(e, "echo MAQUINA_OK; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader", tempo=90)
    if "MAQUINA_OK" in out:
        print(out.strip())
        return 0
    print("A maquina nao respondeu ao SSH ainda:", (err or out).strip()[:300])
    print("Espere um minuto e tente de novo. Se continuar, confira se a chave SSH esta na conta da Vast (python vast.py conta).")
    return 1


def cmd_enviar(a):
    e = estado()
    src = Path(a.arquivo).resolve()
    if not src.exists():
        sys.exit(f"Nao achei o arquivo: {a.arquivo}")
    dest = a.destino or TRABALHO + "/"
    # cria a pasta de destino e usa so o nome do arquivo, com a pasta dele como diretorio atual:
    # no Windows, uma letra de unidade (C:) confundiria o scp com um endereco de maquina.
    rc, out, err = executar(e, f"mkdir -p '{dest if dest.endswith('/') else os.path.dirname(dest)}'", tempo=90)
    if rc != 0:
        sys.exit("Nao consegui falar com a maquina: " + (err or out).strip()[:300])
    cmd = achar("scp") + opcoes(e, "-P") + [src.name, f"{destino(e)}:{dest}"]
    r = subprocess.run(cmd, cwd=str(src.parent), text=True, capture_output=True)
    if r.returncode != 0:
        sys.exit("Falhou o envio: " + (r.stderr or r.stdout).strip()[:400])
    print(f"Enviado: {src.name} -> {dest}")
    return 0


def cmd_baixar(a):
    e = estado()
    pasta = Path(a.pasta or ".").resolve()
    pasta.mkdir(parents=True, exist_ok=True)
    cmd = achar("scp") + opcoes(e, "-P") + [f"{destino(e)}:{a.arquivo}", "."]
    r = subprocess.run(cmd, cwd=str(pasta), text=True, capture_output=True)
    if r.returncode != 0:
        sys.exit("Falhou o download: " + (r.stderr or r.stdout).strip()[:400])
    print("Baixado em:", pasta / Path(a.arquivo).name)
    return 0


def cmd_subir(a):
    e = estado()
    faltam = [n for n in ARQUIVOS_DA_MAQUINA if not (AQUI / n).exists()]
    if faltam:
        sys.exit("Faltam arquivos na pasta da skill: " + ", ".join(faltam))
    rc, out, err = executar(e, f"mkdir -p {PASTA_REMOTA} {TRABALHO}", tempo=90)
    if rc != 0:
        sys.exit("Nao consegui falar com a maquina: " + (err or out).strip()[:300])
    cmd = achar("scp") + opcoes(e, "-P") + ARQUIVOS_DA_MAQUINA + [f"{destino(e)}:{PASTA_REMOTA}/"]
    r = subprocess.run(cmd, cwd=str(AQUI), text=True, capture_output=True)
    if r.returncode != 0:
        sys.exit("Falhou o envio dos scripts: " + (r.stderr or r.stdout).strip()[:400])
    executar(e, f"chmod +x {PASTA_REMOTA}/*.sh {PASTA_REMOTA}/*.py", tempo=60)
    print(f"Scripts enviados para {PASTA_REMOTA}/ ({', '.join(ARQUIVOS_DA_MAQUINA)})")
    return 0


def cmd_rodar(a):
    e = estado()
    rc, out, err = executar(e, texto_do_comando(a.comando), tempo=a.tempo)
    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if err.strip():
        print(err.strip(), file=sys.stderr)
    return rc


def nome_ok(nome):
    if not nome or not all(c.isalnum() or c in "_-" for c in nome):
        sys.exit("O NOME do comando longo so pode ter letras, numeros, _ e -")
    return nome


def cmd_fundo(a):
    e = estado()
    n = nome_ok(a.nome)
    marca = "EOF_SHEEPRINGAN_" + n
    script = (
        f"mkdir -p {TRABALHO}; cd {TRABALHO}; rm -f {n}.fim {n}.log\n"
        f"cat > {n}.cmd.sh <<'{marca}'\n{ATIVAR}\n{texto_do_comando(a.comando)}\n{marca}\n"
        f"S=$(command -v setsid || true)\n"
        f"$S nohup bash -l -c 'bash {n}.cmd.sh; echo $? > {n}.fim' > {n}.log 2>&1 < /dev/null &\n"
        f"sleep 1; echo iniciado {n}\n"
    )
    rc, out, err = executar(e, script, tempo=120)
    print(out.strip() or err.strip())
    return rc


def ler_log(e, n, linhas):
    script = (f"cd {TRABALHO} 2>/dev/null || exit 3; tail -n {int(linhas)} {n}.log 2>/dev/null; "
              f"if [ -f {n}.fim ]; then echo \"[terminou com codigo $(cat {n}.fim)]\"; else echo '[ainda rodando]'; fi")
    return executar(e, script, tempo=90)


def cmd_log(a):
    e = estado()
    rc, out, err = ler_log(e, nome_ok(a.nome), a.linhas)
    print(out.rstrip() or err.strip())
    return 0


def cmd_espera(a):
    e = estado()
    n = nome_ok(a.nome)
    fim = time.time() + a.max * 60
    while True:
        rc, out, err = ler_log(e, n, 12)
        if "[terminou com codigo" in out:
            print(out.rstrip())
            codigo = out.rsplit("[terminou com codigo", 1)[1].split("]")[0].strip()
            return 0 if codigo == "0" else 1
        if time.time() > fim:
            print(out.rstrip())
            print(f"[passaram {a.max} min e ainda esta rodando. Chame `espera {n}` de novo.]")
            return 3
        time.sleep(20)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("testar").set_defaults(f=cmd_testar)
    sub.add_parser("subir").set_defaults(f=cmd_subir)
    p = sub.add_parser("enviar"); p.add_argument("arquivo"); p.add_argument("destino", nargs="?"); p.set_defaults(f=cmd_enviar)
    p = sub.add_parser("baixar"); p.add_argument("arquivo"); p.add_argument("pasta", nargs="?"); p.set_defaults(f=cmd_baixar)
    p = sub.add_parser("rodar"); p.add_argument("comando"); p.add_argument("--tempo", type=int, default=300); p.set_defaults(f=cmd_rodar)
    p = sub.add_parser("fundo"); p.add_argument("nome"); p.add_argument("comando"); p.set_defaults(f=cmd_fundo)
    p = sub.add_parser("log"); p.add_argument("nome"); p.add_argument("--linhas", type=int, default=30); p.set_defaults(f=cmd_log)
    p = sub.add_parser("espera"); p.add_argument("nome"); p.add_argument("--max", type=float, default=8); p.set_defaults(f=cmd_espera)
    a = ap.parse_args()
    sys.exit(a.f(a))


if __name__ == "__main__":
    main()
