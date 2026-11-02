"""vast.py contra uma ferramenta vastai de mentira: confere filtros, estimativa, travas de dinheiro e apagar."""
import json
import sys
import unittest

from ajudas import Casa, TESTES, rodar


def oferta(idn, dph, down_cost, **extra):
    o = {"id": idn, "gpu_name": "RTX 4090", "gpu_ram": 24564, "cpu_ram": 128000, "geolocation": "Quebec, CA", "dph_total": dph,
         "inet_down_cost": down_cost, "inet_down": 800, "reliability2": 0.995, "min_bid": dph * 0.8}
    o.update(extra)
    return o


class TesteVast(Casa):
    def setUp(self):
        super().setUp()
        self.estado = self.tmp / "estado.json"
        self.log = self.tmp / "chamadas.jsonl"
        self.escrever({"ofertas": [oferta(1, 0.40, 0.039), oferta(2, 0.50, 0.003), oferta(3, 0.30, 0.039)], "instancias": [], "credito": 12.0,
                       "chave_na_conta": ""})

    def escrever(self, d):
        self.estado.write_text(json.dumps(d), encoding="utf-8")

    def estado_atual(self):
        return json.loads(self.estado.read_text(encoding="utf-8"))

    def chamadas(self):
        return [json.loads(l) for l in self.log.read_text(encoding="utf-8").splitlines()] if self.log.exists() else []

    def vast(self, *args):
        env = self.env_base()
        env.update({"SHEEPRINGAN_VASTAI": json.dumps([sys.executable, str(TESTES / "vastai_falso.py")]),
                    "VASTAI_FALSO_ESTADO": str(self.estado), "VASTAI_FALSO_LOG": str(self.log),
                    "SHEEPRINGAN_CHAVE": str(self.tmp / "ssh" / "chave")})
        return rodar("vast.py", *args, env=env)

    # ---- ofertas
    def test_estimativa_pesa_o_download_e_ordena_pelo_total(self):
        r = self.vast("ofertas", "--json", "--horas", "2")
        self.assertEqual(r.returncode, 0, r.stderr)
        lista = json.loads(r.stdout)
        # oferta 2: 2*0,50 + 52*0,003 = 1,16 | oferta 1: 2*0,40 + 52*0,039 = 2,83 | oferta 3: 0,60 + 2,03 = 2,63
        self.assertEqual([x["oferta"] for x in lista], [2, 3, 1])
        self.assertAlmostEqual(lista[0]["custo_estimado"], 1.16, places=2)
        self.assertAlmostEqual(lista[0]["custo_do_download"], 0.156, places=3)

    def test_busca_pede_4090_disco_e_exclui_os_paises_da_licenca(self):
        self.vast("ofertas", "--json")
        busca = next(c for c in self.chamadas() if c[:2] == ["search", "offers"])
        q = busca[2]
        self.assertIn("gpu_name=RTX_4090", q)
        self.assertIn("disk_space>=140", q)
        self.assertIn("cpu_ram>=64", q)
        for pais in ("US", "GB", "KR", "DE", "FR", "EE", "SE", "PL"):
            self.assertRegex(q, r"notin \[[^\]]*\b" + pais + r"\b")
        self.assertNotRegex(q, r"notin \[[^\]]*\bBR\b")
        self.assertIn("--storage", busca)
        self.assertEqual(busca[busca.index("--storage") + 1], "140")

    def test_ampliar_troca_o_filtro_de_placa(self):
        self.vast("ofertas", "--json", "--ampliar")
        q = next(c for c in self.chamadas() if c[:2] == ["search", "offers"])[2]
        self.assertIn("compute_cap>=890", q)
        self.assertNotIn("gpu_name=RTX_4090", q)

    def test_interruptivel_usa_type_bid(self):
        self.vast("ofertas", "--json", "--tipo", "interruptivel")
        busca = next(c for c in self.chamadas() if c[:2] == ["search", "offers"])
        self.assertIn("bid", busca)

    # ---- alugar: travas de dinheiro
    def test_alugar_sem_busca_previa_recusa(self):
        r = self.vast("alugar", "2", "--confirmo")
        self.assertEqual(r.returncode, 2)
        self.assertFalse([c for c in self.chamadas() if c[:2] == ["create", "instance"]])

    def test_alugar_sem_confirmo_nao_gasta(self):
        self.vast("ofertas", "--json")
        r = self.vast("alugar", "2")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--confirmo", r.stdout)
        self.assertFalse([c for c in self.chamadas() if c[:2] == ["create", "instance"]])

    def test_alugar_oferta_que_nao_foi_mostrada_recusa(self):
        self.vast("ofertas", "--json", "--quantas", "1")  # so a oferta 2 foi mostrada
        r = self.vast("alugar", "1", "--confirmo")
        self.assertEqual(r.returncode, 2)
        self.assertFalse([c for c in self.chamadas() if c[:2] == ["create", "instance"]])

    def test_alugar_recusa_se_o_preco_subiu(self):
        self.vast("ofertas", "--json")
        d = self.estado_atual()
        d["ofertas"][1]["dph_total"] = 0.90
        self.escrever(d)
        r = self.vast("alugar", "2", "--confirmo")
        self.assertEqual(r.returncode, 2)
        self.assertIn("subiu", r.stdout)
        self.assertFalse([c for c in self.chamadas() if c[:2] == ["create", "instance"]])

    def test_alugar_recusa_se_a_oferta_sumiu(self):
        self.vast("ofertas", "--json")
        d = self.estado_atual()
        d["ofertas"] = [o for o in d["ofertas"] if o["id"] != 2]
        self.escrever(d)
        r = self.vast("alugar", "2", "--confirmo")
        self.assertEqual(r.returncode, 2)
        self.assertFalse([c for c in self.chamadas() if c[:2] == ["create", "instance"]])

    def test_alugar_de_verdade_cria_espera_e_grava_o_endereco(self):
        self.vast("ofertas", "--json")
        r = self.vast("alugar", "2", "--confirmo")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        criar = next(c for c in self.chamadas() if c[:2] == ["create", "instance"])
        self.assertEqual(criar[2], "2")
        for par in (["--image", "vastai/pytorch:latest"], ["--disk", "140"], ["--label", "sheepringan"]):
            self.assertEqual(criar[criar.index(par[0]) + 1], par[1])
        for flag in ("--ssh", "--direct", "--cancel-unavail"):
            self.assertIn(flag, criar)
        self.assertNotIn("--bid_price", criar)
        e = json.loads((self.casa / "maquina.json").read_text(encoding="utf-8"))
        self.assertEqual((e["id"], e["host"], e["port"]), (777, "127.0.0.1", 2222))
        self.assertNotIn("key", json.dumps(e).lower().replace("chave", ""))

    def test_alugar_interruptivel_manda_o_lance(self):
        self.vast("ofertas", "--json", "--tipo", "interruptivel")
        r = self.vast("alugar", "2", "--confirmo")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        criar = next(c for c in self.chamadas() if c[:2] == ["create", "instance"])
        self.assertIn("--bid_price", criar)
        self.assertGreaterEqual(float(criar[criar.index("--bid_price") + 1]), 0.5 * 0.8)

    def test_falha_ao_criar_nao_grava_maquina(self):
        self.vast("ofertas", "--json")
        d = self.estado_atual()
        d["falhar_criar"] = True
        self.escrever(d)
        r = self.vast("alugar", "2", "--confirmo")
        self.assertEqual(r.returncode, 1)
        self.assertFalse((self.casa / "maquina.json").exists())

    # ---- destruir e status
    def test_destruir_pede_confirmacao_e_depois_confere(self):
        d = self.estado_atual()
        d["instancias"] = [{"id": 777, "gpu_name": "RTX 4090", "actual_status": "running", "dph_total": 0.4, "label": "sheepringan"}]
        self.escrever(d)
        self.gravar_maquina()
        r = self.vast("destruir", "777")
        self.assertEqual(r.returncode, 2)
        self.assertFalse([c for c in self.chamadas() if c[:2] == ["destroy", "instance"]])
        r = self.vast("destruir", "777", "--confirmo")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("nao ha mais nenhuma maquina cobrando", r.stdout)
        self.assertFalse((self.casa / "maquina.json").exists())

    def instancia_777(self, **extra):
        d = self.estado_atual()
        d["instancias"] = [{"id": 777, "gpu_name": "RTX 4090", "actual_status": "running", "dph_total": 0.4, "label": "sheepringan"}]
        d.update(extra)
        self.escrever(d)

    def test_destruir_nao_depende_de_resposta_de_teclado(self):
        # a ferramenta de verdade aborta sem apagar se ninguem responde; aqui ela so apaga porque o script manda -y e um "y"
        self.instancia_777()
        r = self.vast("destruir", "777", "--confirmo")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        destroy = next(c for c in self.chamadas() if c[:2] == ["destroy", "instance"])
        self.assertIn("-y", destroy)
        self.assertEqual(self.estado_atual()["instancias"], [])

    def test_destruir_com_ferramenta_antiga_que_nao_conhece_o_y(self):
        self.instancia_777(sem_flag_y=True)
        r = self.vast("destruir", "777", "--confirmo")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        tentativas = [c for c in self.chamadas() if c[:2] == ["destroy", "instance"]]
        self.assertEqual(len(tentativas), 2)
        self.assertNotIn("-y", tentativas[1])
        self.assertEqual(self.estado_atual()["instancias"], [])

    def test_destruir_avisa_se_a_ferramenta_abortou(self):
        self.instancia_777(sempre_aborta=True)
        r = self.vast("destruir", "777", "--confirmo")
        self.assertEqual(r.returncode, 1)
        self.assertIn("abortou", r.stdout)
        self.assertEqual(len(self.estado_atual()["instancias"]), 1)

    def test_status_avisa_que_parada_ainda_cobra(self):
        d = self.estado_atual()
        d["instancias"] = [{"id": 5, "gpu_name": "RTX 4090", "actual_status": "exited", "dph_total": 0.09, "label": "x", "start_date": 1}]
        self.escrever(d)
        r = self.vast("status")
        self.assertIn("parada continua cobrando", r.stdout)

    def test_gastos_soma_por_tipo(self):
        r = self.vast("gastos")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("0,50", r.stdout)  # 0,30 + 0,05 + 0,14 + 0,01
        chamada = next(c for c in self.chamadas() if c[:2] == ["show", "invoices-v1"])
        self.assertTrue(chamada[chamada.index("-s") + 1].isdigit())  # datas como numero: a ferramenta da Vast quebra com texto

    # ---- conta: nunca imprime segredo
    def test_conta_nao_imprime_email_nem_chave_privada(self):
        r = self.vast("conta")
        todo = r.stdout + r.stderr
        self.assertNotIn("nao-deve-aparecer", todo)
        self.assertNotIn("SEGREDO", todo)
        self.assertIn("US$ 12,00", todo)
        self.assertIn("FALTA", todo)  # ainda nao tem chave SSH


if __name__ == "__main__":
    unittest.main()
