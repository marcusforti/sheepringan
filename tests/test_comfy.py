"""objeto.py, trocar_pessoa.py e relay.py contra um ComfyUI de mentira, usando os workflows de verdade do Openjutsu.

Os workflows nao ficam neste repositorio. Para rodar estes testes, aponte para um clone do Openjutsu (na versao testada):
    SHEEPRINGAN_OPENJUTSU=/caminho/openjutsu          (pasta com workflows/object.api.json e simple.api.json)
    SHEEPRINGAN_RELAY_JSON=/caminho/H3-Character-Swap.api.json   (do repositorio h3-relay, example_workflows/toolkit)
Sem isso, os testes correspondentes sao pulados.
"""
import http.server
import json
import os
import shutil
import sys
import threading
import unittest
from pathlib import Path

from ajudas import Casa, SCRIPTS, rodar

OJ = os.environ.get("SHEEPRINGAN_OPENJUTSU")
RELAY = os.environ.get("SHEEPRINGAN_RELAY_JSON")


class ComfyFalso:
    def __init__(self, erro=False):
        recebidos = self.recebidos = []
        mensagens = [["execution_error", {"exception_message": "sem memoria"}]] if erro else []

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                corpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                recebidos.append(corpo)
                self._json({"prompt_id": "abc"})

            def do_GET(self):
                self._json({"abc": {"status": {"status_str": "error" if mensagens else "success", "completed": not mensagens, "messages": mensagens},
                                    "outputs": {"67": {"h3_chain_active_scene": [{"run_name": "edit_teste"}]}}}})

            def _json(self, d):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(d).encode())

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def fechar(self):
        self.srv.shutdown()
        self.srv.server_close()


class Base(Casa):
    def setUp(self):
        super().setUp()
        self.comfy = ComfyFalso()
        self.addCleanup(self.comfy.fechar)
        self.entrada = self.tmp / "input"
        self.entrada.mkdir()
        for n in ("v.mp4", "f.png"):
            (self.tmp / n).write_bytes(b"x")

    def rodar_script(self, nome, *args):
        # o objeto.py espera 15 s entre as consultas; nos testes usamos uma copia sem a espera
        src = (SCRIPTS / nome).read_text(encoding="utf-8").replace("time.sleep(15)", "time.sleep(0)")
        copia = self.tmp / nome
        copia.write_text(src, encoding="utf-8")
        shutil.copy(SCRIPTS / "comfy_api.py", self.tmp / "comfy_api.py")
        import subprocess
        e = dict(os.environ, PYTHONUTF8="1")
        return subprocess.run([sys.executable, str(copia), *map(str, args), "--comfy", self.comfy.url, "--entrada", str(self.entrada)],
                              capture_output=True, text=True, encoding="utf-8", cwd=self.tmp, env=e, timeout=60)

    def postado(self):
        self.assertEqual(len(self.comfy.recebidos), 1)
        corpo = self.comfy.recebidos[0]
        self.assertEqual(corpo["client_id"], "sheepringan")
        return corpo["prompt"]

    @staticmethod
    def titulo(g, t):
        return next(n for n in g.values() if n.get("_meta", {}).get("title") == t)

    def sem_ligacao_quebrada(self, g):
        for k, n in g.items():
            for c, v in n["inputs"].items():
                if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], int):
                    self.assertIn(v[0], g, f"{k}.{c}")


@unittest.skipUnless(OJ, "defina SHEEPRINGAN_OPENJUTSU")
class TesteObjeto(Base):
    def rodar_objeto(self, *args):
        return self.rodar_script("objeto.py", "--workflow", Path(OJ) / "workflows" / "object.api.json", "--video", self.tmp / "v.mp4", *args)

    def plano(self, g):
        return self.titulo(g, "Object Swap Plan (what to change)")["inputs"]

    def test_roupa(self):
        r = self.rodar_objeto("--modo", "change", "--foto", self.tmp / "f.png", "--rotulo", "roupa", "--alvo", "top", "--sam", "hoodie",
                              "--para", "a red denim jacket", "--desc", "A red denim jacket.", "--margem", "20", "--clip", "6.6")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("RUN edit_teste", r.stdout)
        g = self.postado()
        p = self.plano(g)
        self.assertEqual((p["mode"], p["target"], p["change_to"], p["clip_seconds"], p["keep_outline"]), ("change", "top", "a red denim jacket", 6.6, True))
        self.assertEqual(self.titulo(g, "SAM: what to change")["inputs"]["text"], "hoodie")
        self.assertEqual(self.titulo(g, "Grow mask")["inputs"]["expand"], 20)
        self.assertTrue((self.entrada / "v.mp4").exists() and (self.entrada / "f.png").exists())
        self.sem_ligacao_quebrada(g)

    def test_todos_mantem_todas_as_ocorrencias_e_o_padrao_so_a_maior(self):
        base = ["--modo", "change", "--foto", self.tmp / "f.png", "--alvo", "top", "--sam", "t-shirt, arms", "--para", "a jacket", "--clip", "2.5"]
        self.assertEqual(self.rodar_objeto(*base).returncode, 0)
        g = self.postado()
        self.assertEqual(self.titulo(g, "Tracked area")["inputs"]["max_people"], 1)
        self.comfy.recebidos.clear()
        self.assertEqual(self.rodar_objeto(*base, "--todos").returncode, 0)
        g = self.postado()
        self.assertEqual(self.titulo(g, "Tracked area")["inputs"]["max_people"], 0)
        self.assertEqual(self.titulo(g, "SAM: what to change")["inputs"]["text"], "t-shirt, arms")

    def test_cenario_inverte_a_mascara(self):
        r = self.rodar_objeto("--modo", "background", "--foto", self.tmp / "f.png", "--rotulo", "fundo", "--alvo", "person", "--sam", "person",
                              "--para", "a dark office", "--desc", "A dark office.", "--margem", "10", "--clip", "2.5")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        g = self.postado()
        self.assertTrue(self.titulo(g, "Grow mask")["inputs"]["flip_input"])
        self.assertEqual(self.plano(g)["mode"], "background")
        self.sem_ligacao_quebrada(g)

    def test_adicionar_usa_caixa_fixa_e_tira_o_sam(self):
        r = self.rodar_objeto("--modo", "add", "--foto", self.tmp / "f.png", "--rotulo", "mesa", "--alvo", "on the wooden table",
                              "--para", "a tiny living 3D cyborg sheep character", "--desc", "A tiny cyborg sheep.", "--margem", "2", "--clip", "3.05",
                              "--caixa", "0.30,0.41,0.37,0.33", "--acao", "She stands on the table and waves.")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        g = self.postado()
        p = self.plano(g)
        self.assertEqual(p["mode"], "add")
        self.assertFalse(p["keep_outline"])
        self.assertEqual(json.loads(p["placement"]), [{"frame": 0, "x": 0.3, "y": 0.41, "width": 0.37, "height": 0.33}])
        self.assertTrue(any(n["class_type"] == "H3ObjectPlacementMask" for n in g.values()))
        self.assertFalse(any(n.get("_meta", {}).get("title") == "SAM: what to change" for n in g.values()))
        self.sem_ligacao_quebrada(g)

    def test_remover_nao_leva_foto(self):
        r = self.rodar_objeto("--modo", "remove", "--rotulo", "limpo", "--alvo", "backpack", "--sam", "backpack", "--para", "a plain wall", "--clip", "2.5")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        g = self.postado()
        self.assertEqual(self.plano(g)["mode"], "remove")
        self.assertFalse(any(n.get("_meta", {}).get("title") == "Picture 1" for n in g.values()))
        self.sem_ligacao_quebrada(g)


@unittest.skipUnless(OJ, "defina SHEEPRINGAN_OPENJUTSU")
class TesteTrocarPessoa(Base):
    def rodar_troca(self, *args):
        return self.rodar_script("trocar_pessoa.py", "--workflow", Path(OJ) / "workflows" / "simple.api.json", "--video", self.tmp / "v.mp4",
                                 "--foto", self.tmp / "f.png", *args)

    def test_sem_chapeu_e_com_lip_sync(self):
        r = self.rodar_troca("--rotulo", "troca", "--papel", "the singer", "--seed", "7")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        g = self.postado()
        titulos = {n.get("_meta", {}).get("title") for n in g.values()}
        for t in ("SAM: hats", "People + hats", "No lip-sync in the prompt", "Mute the clip audio H3 hears"):
            self.assertNotIn(t, titulos)
        plano = self.titulo(g, "Swap Plan (roles, seed, size)")["inputs"]
        self.assertEqual((plano["roles"], plano["seed"], plano["clip_seconds"], plano["resolution"]), ("the singer", 7, 6, "736p"))
        grow = self.titulo(g, "Grow mask (~4% of the frame)")["inputs"]
        self.assertEqual((grow["expand"], grow["mask"][0]), (40, next(k for k, n in g.items() if n.get("_meta", {}).get("title") == "Main person (+ headroom)")))
        self.assertEqual(self.titulo(g, "Final Video")["inputs"]["filename"], "troca")
        self.sem_ligacao_quebrada(g)

    def test_descricao_fixa_alarga_a_margem(self):
        r = self.rodar_troca("--desc", "A tall woman.")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        g = self.postado()
        self.assertEqual(self.titulo(g, "Grow mask (~4% of the frame)")["inputs"]["expand"], 60)
        self.assertTrue(self.titulo(g, "Describe picture 1")["inputs"]["prompt"].endswith("A tall woman."))

    def test_workflow_mudado_falha_com_mensagem_clara(self):
        g = json.loads((Path(OJ) / "workflows" / "simple.api.json").read_text(encoding="utf-8"))
        for n in g.values():
            if n.get("_meta", {}).get("title") == "Final Video":
                n["_meta"]["title"] = "Outro nome"
        mudado = self.tmp / "mudado.json"
        mudado.write_text(json.dumps(g), encoding="utf-8")
        r = self.rodar_script("trocar_pessoa.py", "--workflow", mudado, "--video", self.tmp / "v.mp4", "--foto", self.tmp / "f.png")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Final Video", r.stderr)
        self.assertEqual(self.comfy.recebidos, [])


@unittest.skipUnless(RELAY, "defina SHEEPRINGAN_RELAY_JSON")
class TesteRelay(Base):
    def test_campos_do_relay(self):
        r = self.rodar_script("relay.py", "--workflow", RELAY, "--video", self.tmp / "v.mp4", "--ref", self.tmp / "f.png", "--rotulo", "r1",
                              "--prompt", "Replace the selected person.", "--seed", "5", "--mem", "13", "--expandir", "120", "--sem-adaptador")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        g = self.postado()
        self.assertEqual(g["save"]["inputs"]["filename_prefix"], "relay/r1")
        self.assertEqual(g["reference_conditioning"]["inputs"]["prompt"], "Replace the selected person.")
        self.assertEqual((g["plan"]["inputs"]["seed"], g["sampling_memory"]["inputs"]["activation_memory_gib"], g["expand_mask"]["inputs"]["expansion_px"]), (5, 13.0, 120))
        self.assertEqual(g["schedule"]["inputs"]["model"], ["turbo", 0])
        self.sem_ligacao_quebrada(g)


class TesteComfyApi(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(SCRIPTS))
        self.addCleanup(sys.path.remove, str(SCRIPTS))
        import comfy_api
        self.api = comfy_api

    def test_comfy_desligado_da_erro_claro(self):
        with self.assertRaises(SystemExit) as c:
            self.api.enviar({}, "http://127.0.0.1:1")
        self.assertEqual(c.exception.code, 2)

    def test_erro_de_execucao_devolve_1_e_mostra_o_motivo(self):
        import contextlib
        import io
        comfy = ComfyFalso(erro=True)
        self.addCleanup(comfy.fechar)
        pid = self.api.enviar({"1": {"class_type": "X", "inputs": {}}}, comfy.url)
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            codigo = self.api.esperar(pid, comfy.url, espera_max=30, intervalo=0)
        self.assertEqual(codigo, 1)
        self.assertIn("ERRO_EXEC", saida.getvalue())
        self.assertIn("sem memoria", saida.getvalue())

    def test_ligacao_quebrada_e_pega_antes_de_gastar_gpu(self):
        with self.assertRaises(SystemExit) as c:
            self.api.conferir_ligacoes({"1": {"inputs": {"a": ["99", 0]}}})
        self.assertIn("quebrada", str(c.exception))


if __name__ == "__main__":
    unittest.main()
