"""Uma ferramenta `vastai` de mentira para os testes. Nada sai do computador e nada custa dinheiro.

O estado fica num arquivo JSON (VASTAI_FALSO_ESTADO) e cada chamada e anotada em VASTAI_FALSO_LOG.
"""
import json
import os
import sys
from pathlib import Path

estado_arq = Path(os.environ["VASTAI_FALSO_ESTADO"])
log_arq = Path(os.environ["VASTAI_FALSO_LOG"])
args = sys.argv[1:]
with log_arq.open("a", encoding="utf-8") as f:
    f.write(json.dumps(args) + "\n")
st = json.loads(estado_arq.read_text(encoding="utf-8"))


def salvar():
    estado_arq.write_text(json.dumps(st), encoding="utf-8")


def saida(x):
    print(json.dumps(x))


cmd = args[0] if args[0] == "ssh-url" else " ".join(args[:2])
if cmd == "search offers":
    saida(st["ofertas"])
elif cmd == "show user":
    saida({"credit": st.get("credito", 10.0), "email": "nao-deve-aparecer@exemplo.test"})
elif cmd == "show ssh-keys":
    saida([{"id": 1, "public_key": st.get("chave_na_conta", ""), "private_key": "SEGREDO-NAO-DEVE-APARECER"}])
elif cmd == "show instances":
    saida(st["instancias"])
elif cmd == "show instance":
    idn = int(args[2])
    achada = [i for i in st["instancias"] if i["id"] == idn]
    saida(achada[0] if achada else {})
elif cmd == "create instance":
    if st.get("falhar_criar"):
        saida({"success": False, "error": "no_such_ask"})
        sys.exit(1)
    novo = {"id": 777, "gpu_name": "RTX 4090", "actual_status": "running", "dph_total": st.get("preco_criacao", 0.4), "label": "sheepringan"}
    st["instancias"].append(novo)
    salvar()
    saida({"success": True, "new_contract": 777})
elif cmd == "ssh-url":
    print("ssh://root@127.0.0.1:2222")
elif cmd == "destroy instance":
    # Igual a ferramenta de verdade: pergunta [y/N] e, sem resposta, ABORTA sem apagar e sai com codigo 0.
    idn = int(args[2])
    tem_y = "-y" in args or "--yes" in args
    if st.get("sem_flag_y") and tem_y:  # versao antiga, que nao conhece o -y
        print("vastai: error: unrecognized arguments: -y", file=sys.stderr)
        sys.exit(2)
    resposta = "y" if tem_y else sys.stdin.readline().strip().lower()
    if resposta != "y" or st.get("sempre_aborta"):
        print("Aborted.")
        sys.exit(0)
    st["instancias"] = [i for i in st["instancias"] if i["id"] != idn]
    salvar()
    print("destroying instance %d." % idn)
elif cmd == "show invoices-v1":
    saida({"count": 1, "next_token": None, "results": [{
        "source": "instance-777", "metadata": {"label": "sheepringan"},
        "items": [{"type": "gpu", "amount": 0.30}, {"type": "disk", "amount": 0.05}, {"type": "bwd", "amount": 0.14}, {"type": "bwu", "amount": 0.01}]}]})
else:
    print("comando nao previsto no teste:", args, file=sys.stderr)
    sys.exit(2)
