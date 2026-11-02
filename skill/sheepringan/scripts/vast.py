#!/usr/bin/env python3
"""Vast.ai sem dor de cabeca: confere a conta, procura maquina, estima o custo, aluga e apaga.

Roda no SEU computador. So biblioteca padrao. Precisa da ferramenta da Vast: pip install vastai
No Mac e no Linux, use python3.

  python vast.py conta [--criar-chave] [--registrar-chave]
  python vast.py ofertas [--perfil basico|relay] [--horas 2] [--tipo fixa|interruptivel] [--ampliar] [--json]
  python vast.py alugar OFERTA --confirmo [--lance US$/h]     (gasta dinheiro: so depois do sim da pessoa)
  python vast.py status
  python vast.py gastos [--desde AAAA-MM-DD]
  python vast.py destruir ID --confirmo                       (apaga tudo que estava na maquina)

Todo valor em dolar americano, como a Vast cobra. Os precos mudam o tempo todo: use sempre `ofertas` na hora.
"""
import argparse
import calendar
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

for _f in (sys.stdout, sys.stderr):
    if hasattr(_f, "reconfigure"):
        _f.reconfigure(encoding="utf-8")

IMAGEM = "vastai/pytorch:latest"
ROTULO = "sheepringan"
DISCO_GB = 140
# A licenca do MiniMax H3 so vale fora da Uniao Europeia, do Reino Unido, da Coreia do Sul e dos Estados Unidos.
# A maquina nao pode ficar nesses lugares (o uso e o resultado tambem nao).
PAISES_FORA = (
    "AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE "  # Uniao Europeia
    "GF GP MQ RE YT AX "  # regioes da UE fora da Europa continental e Aland
    "GB KR US PR GU VI AS MP UM"  # Reino Unido, Coreia do Sul, Estados Unidos e seus territorios
).split()
# GB que a instalacao baixa (medido: 52 GB no basico; o relay e estimativa: o basico mais ~23 GB)
GB_BAIXAR = {"basico": 52, "relay": 75}
CASA = Path(os.environ.get("SHEEPRINGAN_HOME") or (Path.home() / ".sheepringan"))
CHAVE = Path(os.environ.get("SHEEPRINGAN_CHAVE") or (Path.home() / ".ssh" / "vast_ed25519"))


# ---------------------------------------------------------------- utilidades
def num(x, casas=2):
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def usd(x, casas=2):
    return "US$ " + num(x, casas)


def prefixo_vast():
    env = os.environ.get("SHEEPRINGAN_VASTAI")
    if env:
        return json.loads(env) if env.lstrip().startswith("[") else [env]
    achado = shutil.which("vastai")
    return [achado] if achado else None


def sem_cli():
    print("FALTA: a ferramenta da Vast (vastai) nao esta instalada neste computador.")
    print("  Instale com:  pip install vastai")
    print("  Se der 'comando nao encontrado' depois, feche e abra o terminal.")
    sys.exit(3)


def chamar(*args, bruto=True, tempo=180):
    """Roda a ferramenta vastai. Devolve (codigo, saida, erro). O UTF-8 evita o erro 'charmap' do Windows."""
    pre = prefixo_vast()
    if not pre:
        sem_cli()
    cmd = pre + list(args) + (["--raw"] if bruto else [])
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NO_COLOR="1")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=tempo)
    return r.returncode, r.stdout, r.stderr


def json_de(texto):
    texto = (texto or "").strip()
    if not texto:
        return None
    try:
        return json.loads(texto)
    except ValueError:
        pass
    for ini in (texto.find("{"), texto.find("[")):
        if ini >= 0:
            try:
                return json.JSONDecoder().raw_decode(texto[ini:])[0]
            except ValueError:
                continue
    return None


def ler_estado():
    p = CASA / "maquina.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def gravar_estado(d):
    CASA.mkdir(parents=True, exist_ok=True)
    (CASA / "maquina.json").write_text(json.dumps(d, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- conta
def chave_publica():
    pub = Path(str(CHAVE) + ".pub")
    return pub.read_text(encoding="utf-8").strip() if pub.exists() else None


def corpo_da_chave(texto):
    partes = (texto or "").split()
    return partes[1] if len(partes) >= 2 else None


def cmd_conta(a):
    faltas = 0
    if not prefixo_vast():
        print("FALTA: a ferramenta da Vast (vastai) nao esta instalada. Instale com:  pip install vastai")
        return 1
    print("OK: ferramenta vastai encontrada.")

    rc, out, _ = chamar("show", "user")
    d = json_de(out)
    if rc != 0 or not isinstance(d, dict) or "credit" not in d:
        print("FALTA: a chave da API da Vast nao esta configurada (ou esta errada).")
        print("  1) Entre em https://cloud.vast.ai/manage-keys/ e clique em +New para criar uma chave de API.")
        print("  2) Rode:  vastai set api-key SUA_CHAVE   (a pessoa cola a chave no terminal dela; nao mande a chave pelo chat)")
        faltas += 1
    else:
        credito = float(d.get("credit") or 0)
        print(f"OK: conta da Vast conectada. Credito: {usd(credito)}.")
        if credito < 5:
            print("ATENCAO: pouco credito. A Vast pede pelo menos US$ 5 por recarga (Billing > Add Credit, em https://cloud.vast.ai/billing/).")
            print("  Uma sessao costuma custar de US$ 1 a US$ 5, quase tudo no download dos modelos. Veja `ofertas`.")
            faltas += 1

    pub = chave_publica()
    if not pub:
        if a.criar_chave:
            CHAVE.parent.mkdir(parents=True, exist_ok=True)
            r = subprocess.run(["ssh-keygen", "-t", "ed25519", "-f", str(CHAVE), "-N", "", "-C", "sheepringan"], capture_output=True, text=True)
            if r.returncode != 0:
                print("FALTA: nao consegui criar a chave SSH:", (r.stderr or r.stdout).strip()[:300])
                print("  No Windows 10/11, ative o 'Cliente OpenSSH' em Configuracoes > Aplicativos > Recursos opcionais.")
                return 1
            pub = chave_publica()
            print(f"OK: chave SSH criada em {CHAVE} (a parte privada nunca sai do seu computador).")
        else:
            print(f"FALTA: ainda nao existe a chave SSH ({CHAVE}). Rode de novo com --criar-chave.")
            faltas += 1
    else:
        print(f"OK: chave SSH encontrada ({CHAVE}).")

    if pub:
        rc, out, _ = chamar("show", "ssh-keys")
        lista = json_de(out)
        corpo = corpo_da_chave(pub)
        # nao imprimir nada alem da comparacao: a resposta da Vast pode trazer campos sensiveis
        na_conta = isinstance(lista, list) and any(corpo_da_chave(k.get("public_key", "")) == corpo for k in lista if isinstance(k, dict))
        if na_conta:
            print("OK: a chave SSH ja esta cadastrada na conta da Vast.")
        elif a.registrar_chave:
            rc, out, err = chamar("create", "ssh-key", pub, bruto=False)
            if rc == 0:
                print("OK: chave SSH cadastrada na conta da Vast.")
            else:
                print("FALTA: nao consegui cadastrar a chave:", (err or out).strip()[:300])
                faltas += 1
        else:
            print("FALTA: a chave SSH ainda nao esta na conta da Vast. Rode de novo com --registrar-chave")
            print("  (ou cole o conteudo de", str(CHAVE) + ".pub", "em https://cloud.vast.ai/manage-keys/).")
            faltas += 1

    rc, out, _ = chamar("show", "instances")
    inst = json_de(out)
    if isinstance(inst, list) and inst:
        print(f"ATENCAO: ja existe(m) {len(inst)} maquina(s) alugada(s), cobrando agora:")
        for i in inst:
            print(f"  - id {i.get('id')} | {i.get('gpu_name')} | {i.get('actual_status')} | {usd(float(i.get('dph_total') or 0))}/h | rotulo {i.get('label') or '-'}")
    elif isinstance(inst, list):
        print("OK: nenhuma maquina alugada agora (nada cobrando).")

    print("PRONTO" if faltas == 0 else f"FALTAM {faltas} coisa(s) acima.")
    return 0 if faltas == 0 else 1


# ---------------------------------------------------------------- ofertas
def montar_consulta(a):
    p = [
        "num_gpus=1", f"gpu_ram>={a.vram}", f"disk_space>={a.disco}", f"reliability>{a.confiabilidade}",
        "verified=True", "rentable=True", f"cpu_ram>={a.ram}", "cuda_vers>=12.8", "direct_port_count>=1",
        "geolocation notin [" + ",".join(PAISES_FORA) + "]",
    ]
    # RTX 4090 e a unica placa testada. --ampliar aceita a mesma geracao (RTX 40xx e 50xx), sem teste.
    p.append("compute_cap>=890" if a.ampliar else "gpu_name=RTX_4090")
    return " ".join(p)


def buscar(a):
    args = ["search", "offers", montar_consulta(a), "--storage", str(a.disco), "--limit", "500"]
    if a.tipo == "interruptivel":
        args += ["--type", "bid"]
    rc, out, err = chamar(*args)
    d = json_de(out)
    if rc != 0 or not isinstance(d, list):
        print("ERRO: a busca na Vast falhou:", (err or out).strip()[:400])
        sys.exit(1)
    return d


def calcular(o, gb, horas):
    preco_h = float(o.get("dph_total") or 0)  # ja inclui o disco, porque a busca usa --storage
    baixar = gb * float(o.get("inet_down_cost") or 0)
    mbps = max(float(o.get("inet_down") or 0), 1.0)
    return {
        "oferta": o.get("id"),
        "placa": o.get("gpu_name"),
        "vram_gb": round(float(o.get("gpu_ram") or 0) / 1024),
        "ram_gb": round(float(o.get("cpu_ram") or 0) / 1024),
        "onde": o.get("geolocation"),
        "dolar_por_hora": round(preco_h, 4),
        "dolar_por_gb_baixado": round(float(o.get("inet_down_cost") or 0), 5),
        "custo_do_download": round(baixar, 3),
        "mbps": round(mbps),
        "minutos_para_instalar": round(gb * 8000 / mbps / 60 + 5),
        "confiabilidade": round(float(o.get("reliability2") or o.get("reliability") or 0), 3),
        "lance_minimo": round(float(o.get("min_bid") or 0), 4) if o.get("min_bid") else None,
        "custo_estimado": round(horas * preco_h + baixar, 2),
        "por_dia_se_esquecer": round(24 * preco_h, 2),
    }


def cmd_ofertas(a):
    gb = a.gb or GB_BAIXAR[a.perfil]
    brutas = buscar(a)
    linhas = sorted((calcular(o, gb, a.horas) for o in brutas), key=lambda x: (x["custo_estimado"], -x["confiabilidade"]))
    mostrar = linhas[: a.quantas]
    CASA.mkdir(parents=True, exist_ok=True)
    (CASA / "ultima_busca.json").write_text(json.dumps({
        "quando": int(time.time()), "tipo": a.tipo, "disco": a.disco, "vram": a.vram, "ram": a.ram,
        "confiabilidade": a.confiabilidade, "ampliar": a.ampliar, "perfil": a.perfil,
        "ofertas": {str(x["oferta"]): x["dolar_por_hora"] for x in mostrar},
    }, indent=1), encoding="utf-8")
    if a.json:
        print(json.dumps(mostrar, indent=1, ensure_ascii=False))
        return 0
    cond = "RTX 4090" if not a.ampliar else "RTX 40xx/50xx com 16 GB ou mais (sem teste nosso)"
    print(f"Procurei: {cond}, disco {a.disco} GB, {a.ram} GB de RAM ou mais, confiavel, preco {'FIXO' if a.tipo == 'fixa' else 'INTERRUPTIVEL'},")
    print("fora da Uniao Europeia, do Reino Unido, da Coreia do Sul e dos Estados Unidos (exigencia da licenca do modelo).")
    if not linhas:
        print("Nao achei nenhuma maquina com esses filtros agora. Tente de novo mais tarde, ou use --ampliar / --ram 64 (sem teste).")
        return 1
    print(f"Achei {len(linhas)}. As {len(mostrar)} de menor custo para {a.horas:g} h de uso + {gb} GB de modelos para baixar:\n")
    cab = f"{'#':>2}  {'oferta':>9}  {'placa':<9} {'onde':<22} {'US$/h':>6} {'download US$/GB':>15} {'veloc.':>9} {'RAM':>6} {'confiab.':>8}  {'custo estimado':>14}"
    print(cab)
    for i, x in enumerate(mostrar, 1):
        print(f"{i:>2}  {x['oferta']:>9}  {x['placa']:<9} {str(x['onde'])[:22]:<22} {num(x['dolar_por_hora'], 3):>6} {num(x['dolar_por_gb_baixado'], 4):>15} {str(x['mbps']) + ' Mb/s':>9} {str(x['ram_gb']) + ' GB':>6} {num(x['confiabilidade'], 3):>8}  {usd(x['custo_estimado']):>14}")
    m = mostrar[0]
    print(f"\nCusto estimado = {a.horas:g} h x preco por hora + {gb} GB x preco do download. Os precos mudam: isto e uma estimativa, nao uma garantia.")
    print(f"O download dos modelos e a parte que mais varia: de {usd(min(x['custo_do_download'] for x in mostrar))} a {usd(max(x['custo_do_download'] for x in mostrar))} nestas ofertas.")
    print(f"Instalar leva uns {m['minutos_para_instalar']} min na primeira. Se esquecer a maquina ligada: {usd(m['por_dia_se_esquecer'])} por dia.")
    if a.tipo == "interruptivel":
        print("INTERRUPTIVEL = mais barata, mas a Vast pode pausar a sua maquina quando alguem pagar mais. Para a primeira vez, prefira a FIXA.")
        print("  O lance minimo aparece no campo lance_minimo (--json). Ofereca um pouco acima (+10%) com --lance.")
    print("\nMostre estes numeros a pessoa e peca o sim. So depois:  python vast.py alugar OFERTA --confirmo")
    return 0


# ---------------------------------------------------------------- alugar
def parametros_da_ultima_busca():
    p = CASA / "ultima_busca.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    return d


def esperar_no_ar(idn, limite_s=900):
    t0 = time.time()
    ultimo = None
    while time.time() - t0 < limite_s:
        rc, out, _ = chamar("show", "instance", str(idn))
        d = json_de(out)
        d = d[0] if isinstance(d, list) and d else d
        st = d.get("actual_status") if isinstance(d, dict) else None
        if st != ultimo:
            print(f"  estado da maquina: {st}", flush=True)
            ultimo = st
        if st == "running":
            return True
        time.sleep(10)
    return False


def cmd_alugar(a):
    ult = parametros_da_ultima_busca()
    if not ult:
        print("Rode primeiro `ofertas` e mostre os custos a pessoa. O `alugar` so aceita ofertas vistas na ultima busca.")
        return 2
    visto = ult["ofertas"].get(str(a.oferta))
    if visto is None:
        print(f"A oferta {a.oferta} nao estava na ultima lista de `ofertas`. Rode `ofertas` de novo e escolha uma de la.")
        return 2
    if not a.confirmo:
        print(f"Isto ALUGARIA a oferta {a.oferta} (visto: {usd(visto, 3)}/h) e comecaria a cobrar na hora.")
        print("Quando a pessoa disser sim ao custo estimado, rode de novo com --confirmo.")
        return 2

    # repete a mesma busca (mesmos filtros, inclusive o de pais) e confere a oferta e o preco agora
    b = argparse.Namespace(tipo=ult["tipo"], disco=ult["disco"], vram=ult["vram"], ram=ult["ram"],
                           confiabilidade=ult["confiabilidade"], ampliar=ult["ampliar"])
    agora = {str(o.get("id")): o for o in buscar(b)}
    o = agora.get(str(a.oferta))
    if not o:
        print("Essa oferta nao esta mais disponivel (alguem alugou, ou nao passa mais nos filtros). Rode `ofertas` de novo.")
        return 2
    preco = float(o.get("dph_total") or 0)
    if preco > visto * 1.10 + 0.02:
        print(f"O preco subiu: era {usd(visto, 3)}/h e agora e {usd(preco, 3)}/h. Rode `ofertas` e peca o sim de novo.")
        return 2
    cmd = ["create", "instance", str(a.oferta), "--image", IMAGEM, "--disk", str(ult["disco"]), "--ssh", "--direct", "--label", ROTULO, "--cancel-unavail"]
    if ult["tipo"] == "interruptivel":
        minimo = float(o.get("min_bid") or 0)
        lance = a.lance or round(minimo * 1.1, 4)
        if lance < minimo:
            print(f"O lance ({lance}) esta abaixo do minimo ({minimo}).")
            return 2
        cmd += ["--bid_price", str(lance)]
    rc, out, err = chamar(*cmd)
    d = json_de(out)
    idn = d.get("new_contract") if isinstance(d, dict) else None
    if idn is None:
        m = re.search(r"new_contract\D+(\d+)", out or "")
        idn = int(m.group(1)) if m else None
    if rc != 0 or not idn:
        print("ERRO: a Vast nao criou a maquina:", ((err or "") + (out or "")).strip()[:500])
        return 1
    print(f"Maquina {idn} criada. A cobranca ja comecou ({usd(preco, 3)}/h). Esperando ligar (pode levar uns minutos)...")
    if not esperar_no_ar(idn):
        print(f"AVISO: a maquina {idn} ainda nao ficou 'running' em 15 min. Veja `status`. Se nao for ligar, apague: python vast.py destruir {idn} --confirmo")
        gravar_estado({"id": idn, "host": None, "port": None, "usuario": "root", "chave": str(CHAVE)})
        return 1
    rc, out, _ = chamar("ssh-url", str(idn), bruto=False)
    m = re.search(r"ssh://(\w+)@([^:\s]+):(\d+)", out or "")
    if not m:
        print("AVISO: nao consegui o endereco SSH. Saida:", (out or "").strip()[:200])
        gravar_estado({"id": idn, "host": None, "port": None, "usuario": "root", "chave": str(CHAVE)})
        return 1
    gravar_estado({"id": idn, "host": m.group(2), "port": int(m.group(3)), "usuario": m.group(1), "chave": str(CHAVE), "preco_hora": preco})
    # cada maquina tem uma identidade nova: esquece a anterior para o SSH nao reclamar
    try:
        (CASA / "known_hosts").unlink()
    except OSError:
        pass
    print(f"Maquina {idn} no ar. Proximo passo: python remoto.py testar")
    return 0


# ---------------------------------------------------------------- status, gastos, destruir
def listar_instancias():
    rc, out, err = chamar("show", "instances")
    d = json_de(out)
    if rc != 0 or not isinstance(d, list):
        print("ERRO: nao consegui listar as maquinas:", (err or out).strip()[:300])
        sys.exit(1)
    return d


def cmd_status(a):
    inst = listar_instancias()
    if not inst:
        print("Nenhuma maquina alugada agora. Nada esta cobrando.")
        return 0
    total = 0.0
    for i in inst:
        preco = float(i.get("dph_total") or 0)
        total += preco
        desde = float(i.get("start_date") or 0)
        ligada = f"{(time.time() - desde) / 3600:.1f} h" if desde else "?"
        print(f"- id {i.get('id')} | {i.get('gpu_name')} | estado {i.get('actual_status')} | {usd(preco, 3)}/h | ligada ha {ligada} | rotulo {i.get('label') or '-'}")
    print(f"Cobrando agora: {usd(total, 3)} por hora, {usd(total * 24)} por dia. Maquina parada continua cobrando o disco. So apagar encerra a cobranca.")
    return 0


def cmd_gastos(a):
    ate = int(time.time()) + 86400
    if a.desde:
        desde = calendar.timegm(time.strptime(a.desde, "%Y-%m-%d"))
    else:
        desde = ate - 8 * 86400
    # as datas vao como numero: a ferramenta da Vast da erro se receber texto sem a data final
    por = {}
    token = None
    while True:
        args = ["show", "invoices-v1", "--charges", "-s", str(desde), "-e", str(ate), "--limit", "100"]
        if token:
            args += ["-t", token]
        rc, out, err = chamar(*args)
        d = json_de(out)
        if rc != 0 or not isinstance(d, dict):
            print("ERRO: nao consegui ler as cobrancas:", (err or out).strip()[:300])
            return 1
        for r in d.get("results", []):
            quem = r.get("source") or r.get("description") or "?"
            reg = por.setdefault(quem, {"gpu": 0.0, "disk": 0.0, "bwd": 0.0, "bwu": 0.0, "rotulo": (r.get("metadata") or {}).get("label")})
            for it in r.get("items", []):
                if it.get("type") in reg:
                    reg[it["type"]] += float(it.get("amount") or 0)
        token = d.get("next_token")
        if not token:
            break
    if not por:
        print("Nenhuma cobranca nesse periodo.")
        return 0
    print(f"{'maquina':<22} {'GPU':>8} {'disco':>8} {'download':>9} {'upload':>8} {'total':>8}")
    soma = 0.0
    for quem, r in sorted(por.items()):
        t = r["gpu"] + r["disk"] + r["bwd"] + r["bwu"]
        soma += t
        print(f"{quem[:22]:<22} {num(r['gpu']):>8} {num(r['disk']):>8} {num(r['bwd']):>9} {num(r['bwu']):>8} {num(t):>8}   {r['rotulo'] or ''}")
    print(f"Total no periodo: {usd(soma)}. A Vast fecha as cobrancas por dia: a ultima pode demorar um pouco para aparecer.")
    return 0


def cmd_destruir(a):
    if not a.confirmo:
        print(f"Isto APAGA a maquina {a.id} e tudo que esta nela (modelos, videos, resultados). Nao tem volta.")
        print("Baixe os resultados antes. Quando a pessoa confirmar, rode de novo com --confirmo.")
        return 2
    rc, out, err = chamar("destroy", "instance", str(a.id), "-y", bruto=False)
    if rc != 0:
        print("ERRO ao apagar:", (err or out).strip()[:400])
        return 1
    for _ in range(6):
        ids = {str(i.get("id")) for i in listar_instancias()}
        if str(a.id) not in ids:
            break
        time.sleep(5)
    else:
        print(f"AVISO: a maquina {a.id} ainda aparece na lista. Rode `status` daqui a pouco.")
        return 1
    e = ler_estado()
    if e and str(e.get("id")) == str(a.id):
        (CASA / "maquina.json").unlink()
    restantes = listar_instancias()
    if restantes:
        print(f"Maquina {a.id} apagada, mas ainda ha {len(restantes)} maquina(s) cobrando. Rode `status`.")
    else:
        print(f"Maquina {a.id} apagada. Conferido: nao ha mais nenhuma maquina cobrando.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("conta", help="confere a ferramenta, a chave da API, o credito e a chave SSH")
    c.add_argument("--criar-chave", action="store_true")
    c.add_argument("--registrar-chave", action="store_true")
    c.set_defaults(f=cmd_conta)

    o = sub.add_parser("ofertas", help="procura maquinas e estima o custo")
    o.add_argument("--perfil", choices=sorted(GB_BAIXAR), default="basico")
    o.add_argument("--gb", type=float, default=None, help="GB que serao baixados (padrao: 52 no basico, 75 no relay)")
    o.add_argument("--horas", type=float, default=2.0, help="horas de uso previstas (padrao 2)")
    o.add_argument("--tipo", choices=["fixa", "interruptivel"], default="fixa")
    o.add_argument("--disco", type=int, default=DISCO_GB)
    o.add_argument("--vram", type=int, default=16, help="GB de memoria de video, no minimo")
    o.add_argument("--ram", type=int, default=64, help="GB de memoria RAM, no minimo")
    o.add_argument("--confiabilidade", type=float, default=0.98)
    o.add_argument("--ampliar", action="store_true", help="aceita outras placas RTX 40xx/50xx (nao testadas)")
    o.add_argument("--quantas", type=int, default=6)
    o.add_argument("--json", action="store_true")
    o.set_defaults(f=cmd_ofertas)

    al = sub.add_parser("alugar", help="aluga uma oferta da ultima busca (gasta dinheiro)")
    al.add_argument("oferta", type=int)
    al.add_argument("--confirmo", action="store_true", help="so use depois do sim da pessoa ao custo estimado")
    al.add_argument("--lance", type=float, default=None, help="so para interruptivel: US$ por hora")
    al.set_defaults(f=cmd_alugar)

    st = sub.add_parser("status", help="lista as maquinas alugadas e quanto cobram")
    st.set_defaults(f=cmd_status)

    g = sub.add_parser("gastos", help="soma as cobrancas reais por tipo")
    g.add_argument("--desde", default=None, help="AAAA-MM-DD (padrao: ultimos 8 dias)")
    g.set_defaults(f=cmd_gastos)

    d = sub.add_parser("destruir", help="apaga a maquina (e tudo dentro)")
    d.add_argument("id", type=int)
    d.add_argument("--confirmo", action="store_true")
    d.set_defaults(f=cmd_destruir)

    a = ap.parse_args()
    sys.exit(a.f(a))


if __name__ == "__main__":
    main()
