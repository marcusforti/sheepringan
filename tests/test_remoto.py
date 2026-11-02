"""remoto.py e resultado.py com um ssh/scp de mentira: o comando remoto roda de verdade, numa pasta temporaria."""
import json
import sys
import unittest

from ajudas import Casa, SCRIPTS, TESTES, bash_gnu, rodar


@unittest.skipUnless(bash_gnu(), "precisa de um bash de verdade (no Windows, o do Git)")
class TesteRemoto(Casa):
    def setUp(self):
        super().setUp()
        self.gravar_maquina()
        self.env = self.env_base()
        falso = str(TESTES / "ssh_falso.py")
        self.env["SHEEPRINGAN_SSH"] = json.dumps([sys.executable, falso, "ssh"])
        self.env["SHEEPRINGAN_SCP"] = json.dumps([sys.executable, falso, "scp"])

    def r(self, *args, **kw):
        return rodar("remoto.py", *args, env=self.env, **kw)

    def test_testar(self):
        r = self.r("testar")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("MAQUINA_OK", r.stdout)

    def test_comando_com_aspas_cifrao_e_acento_chega_inteiro(self):
        r = self.r("rodar", "echo \"a 'b' $((1+2)) \\\"c\\\" ção\"")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("a 'b' 3 \"c\" ção", r.stdout)

    def test_codigo_de_saida_volta(self):
        self.assertEqual(self.r("rodar", "exit 7").returncode, 7)

    def test_enviar_arquivo_com_espaco_no_nome_e_baixar_de_volta(self):
        origem = self.tmp / "pasta com espaco"
        origem.mkdir()
        f = origem / "meu video.mp4"
        f.write_bytes(b"conteudo")
        r = self.r("enviar", f)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        no_remoto = self.remota / "trabalho" / "meu video.mp4"
        self.assertEqual(no_remoto.read_bytes(), b"conteudo")
        volta = self.tmp / "volta"
        r = self.r("baixar", no_remoto.as_posix(), volta)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((volta / "meu video.mp4").read_bytes(), b"conteudo")

    def test_baixar_arquivo_que_nao_existe_falha_com_mensagem(self):
        r = self.r("baixar", (self.remota / "nada.mp4").as_posix(), self.tmp / "v")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Falhou o download", r.stderr + r.stdout)

    def test_subir_manda_todos_os_scripts_da_maquina(self):
        r = self.r("subir")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for nome in ("objeto.py", "trocar_pessoa.py", "relay.py", "comfy_api.py", "instalar_maquina.sh"):
            self.assertTrue((self.remota / "sheepringan" / nome).exists(), nome)

    def test_fundo_log_e_espera_com_sucesso(self):
        r = self.r("fundo", "t1", "echo comecou; sleep 1; echo acabou")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("iniciado t1", r.stdout)
        r = self.r("espera", "t1", "--max", "1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("acabou", r.stdout)
        self.assertIn("terminou com codigo 0", r.stdout)

    def test_fundo_que_falha_devolve_erro(self):
        self.r("fundo", "t2", "echo vai falhar; exit 3")
        r = self.r("espera", "t2", "--max", "1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("terminou com codigo 3", r.stdout)

    def test_log_de_comando_ainda_rodando(self):
        self.r("fundo", "t3", "echo comeco; sleep 20")
        r = self.r("log", "t3")
        self.assertIn("ainda rodando", r.stdout)
        self.assertIn("comeco", r.stdout)

    def test_comando_vindo_de_arquivo_com_varias_linhas_e_aspas(self):
        arq = self.tmp / "cmd.sh"
        arq.write_text("#!/bin/bash\nX='um valor com espaco'\necho \"$X\"\npython3 -c 'print(1+1)' 2>/dev/null || echo sem-python3\n", encoding="utf-8")
        r = self.r("fundo", "t5", "@" + str(arq))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.r("espera", "t5", "--max", "1")
        self.assertIn("um valor com espaco", r.stdout)
        self.assertEqual(r.returncode, 0)

    def test_arquivo_de_comando_inexistente(self):
        r = self.r("rodar", "@nao-existe.sh")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Nao achei o arquivo do comando", r.stderr + r.stdout)

    def test_nome_com_caracter_perigoso_e_recusado(self):
        r = self.r("fundo", "a;rm -rf x", "echo oi")
        self.assertNotEqual(r.returncode, 0)

    def test_sem_maquina_registrada_explica(self):
        (self.casa / "maquina.json").unlink()
        r = self.r("testar")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("vast.py", r.stderr + r.stdout)


@unittest.skipUnless(bash_gnu(), "precisa de um bash de verdade (no Windows, o do Git)")
class TesteResultado(Casa):
    def setUp(self):
        super().setUp()
        self.gravar_maquina()
        falso = str(TESTES / "ssh_falso.py")
        self.env = dict(self.env_base(), SHEEPRINGAN_SSH=json.dumps([sys.executable, falso, "ssh"]),
                        SHEEPRINGAN_SCP=json.dumps([sys.executable, falso, "scp"]))
        self.saida = self.remota / "ComfyUI" / "output"

    def test_pega_o_video_pronto_com_audio(self):
        pasta = self.saida / "h3_oneclick_edit"
        pasta.mkdir(parents=True)
        (pasta / "lab_00001_.mp4").write_bytes(b"pronto")
        r = rodar("resultado.py", "lab", "--saida", self.tmp / "dl", env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((self.tmp / "dl" / "lab_00001_.mp4").read_bytes(), b"pronto")
        self.assertIn('"tipo": "pronto"', r.stdout)

    def test_cai_para_o_clipe_sem_audio_quando_a_montagem_falhou(self):
        clipes = self.saida / "h3_chains" / "edit_abc" / "generation" / "clips"
        clipes.mkdir(parents=True)
        (clipes / "clip_000.mp4").write_bytes(b"sem audio")
        r = rodar("resultado.py", "lab2", "--run", "edit_abc", "--saida", self.tmp / "dl", env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((self.tmp / "dl" / "lab2_clipe_sem_audio.mp4").read_bytes(), b"sem audio")
        self.assertIn("SEM audio", r.stdout)

    def test_nada_para_baixar(self):
        r = rodar("resultado.py", "nada", "--saida", self.tmp / "dl", env=self.env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Nao achei", r.stdout)

    def test_rotulo_perigoso_e_recusado(self):
        r = rodar("resultado.py", "x;rm", env=self.env)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
