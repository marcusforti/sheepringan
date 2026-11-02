"""Confere o pacote que vai para o GitHub: nada pessoal, textos coerentes, scripts compilando e instaladores funcionando."""
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ajudas import RAIZ, SCRIPTS, bash_gnu

SKILL = RAIZ / "skill" / "sheepringan"

PROIBIDOS = [
    (r"\b55\d{10,11}\b", "telefone real"),
    (r"\(\d{2}\)\s?9?\d{4}-?\d{4}", "telefone real"),
    (r"\b\d{12,}@(lid|s\.whatsapp\.net|g\.us)\b", "jid real"),
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "ip"),
    (r"sk-[A-Za-z0-9_-]{16,}|xi-api-key:\s*[a-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}", "chave"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY", "chave privada"),
    (r"\b[A-Za-z]:\\", "caminho do Windows"),
    (r"(?i)\bD:/(0\d_|[A-Z]{3,})", "caminho local"),
    (r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}", "e-mail"),
]
LIBERADOS = {"127.0.0.1", "noreply@anthropic.com", "nao-deve-aparecer@exemplo.test", "root@127.0.0.1"}
# Nomes de pessoas, clientes e projetos reais ficam num arquivo que nao vai para o GitHub.
LOCAL = Path(__file__).with_name("proibidos.local.txt")
if LOCAL.exists():
    PROIBIDOS += [("(?i)" + l, "item da lista local") for l in LOCAL.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
# O nome do autor so aparece como autor (LICENSE e README), e o login do GitHub so onde ele e necessario (enderecos).
SO_COMO_AUTOR = {"LICENSE", "README.md"}
SO_NOS_ENDERECOS = {"README.md", "instalar.ps1", "instalar.sh", "test_pacote.py"}


def arquivos():
    for p in RAIZ.rglob("*"):
        if p.is_file() and not {"__pycache__", ".git"} & set(p.parts) and p.suffix != ".pyc":
            yield p


class TestSemDadosPessoais(unittest.TestCase):
    def test_nada_pessoal_no_pacote(self):
        achados = []
        for p in arquivos():
            if p.name in ("test_pacote.py", "proibidos.local.txt"):
                continue
            texto = p.read_text(encoding="utf-8", errors="replace")
            for padrao, nome in PROIBIDOS:
                for m in re.finditer(padrao, texto):
                    if m.group(0) not in LIBERADOS:
                        achados.append(f"{p.relative_to(RAIZ)}: {nome}: {m.group(0)}")
            if "Marcus" in texto and p.name not in SO_COMO_AUTOR:
                achados.append(f"{p.relative_to(RAIZ)}: nome do autor fora de LICENSE/README")
            if re.search(r"(?i)marcusforti", texto) and p.name not in SO_NOS_ENDERECOS:
                achados.append(f"{p.relative_to(RAIZ)}: login do GitHub fora dos enderecos")
        self.assertEqual(achados, [])

    def test_lista_local_fica_fora_do_git(self):
        self.assertIn("tests/proibidos.local.txt", (RAIZ / ".gitignore").read_text(encoding="utf-8"))
        texto = Path(__file__).read_text(encoding="utf-8").lower()
        for linha in (LOCAL.read_text(encoding="utf-8").splitlines() if LOCAL.exists() else []):
            if linha.strip() and not linha.startswith("#") and "\\" not in linha and "(" not in linha:
                self.assertNotIn(linha.lower(), texto)

    def test_nao_ha_video_foto_nem_modelo_no_pacote(self):
        pesados = [str(p.relative_to(RAIZ)) for p in arquivos() if p.suffix.lower() in {".mp4", ".mov", ".mkv", ".avi", ".png", ".jpg", ".jpeg", ".safetensors", ".onnx", ".pt"}]
        self.assertEqual(pesados, [])

    def test_nome_antigo_nao_sobrou(self):
        sobras = [str(p.relative_to(RAIZ)) for p in arquivos() if p.name != "test_pacote.py" and re.search(r"(?i)sheep-?jutsu", p.read_text(encoding="utf-8", errors="replace"))]
        self.assertEqual(sobras, [])


class TestTextos(unittest.TestCase):
    def test_skill_tem_nome_e_descricao_validos(self):
        cabeca = (SKILL / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
        self.assertIn("name: sheepringan", cabeca)
        descricao = re.search(r"description: (.+)", cabeca).group(1)
        self.assertLess(len(cabeca), 1024)
        self.assertTrue(descricao.startswith("Use quando"))
        for palavra in ("Vast.ai", "Openjutsu", "roupa", "cenário"):
            self.assertIn(palavra, descricao)

    def test_referencias_citadas_existem(self):
        textos = [(SKILL / "SKILL.md").read_text(encoding="utf-8")] + [p.read_text(encoding="utf-8") for p in (SKILL / "references").glob("*.md")]
        for nome in set(re.findall(r"`(?:references/)?(\d\d-[a-z]+\.md|problemas\.md|medidas\.md)`", "\n".join(textos))):
            self.assertTrue((SKILL / "references" / nome).exists(), nome)

    def test_programas_citados_existem(self):
        textos = [(SKILL / "SKILL.md").read_text(encoding="utf-8")] + [p.read_text(encoding="utf-8") for p in (SKILL / "references").glob("*.md")]
        for nome in set(re.findall(r"SCRIPTS/([a-z_]+\.(?:py|sh))", "\n".join(textos))):
            self.assertTrue((SCRIPTS / nome).exists(), nome)

    def test_programas_citados_nos_comandos_da_maquina_existem(self):
        textos = "\n".join(p.read_text(encoding="utf-8") for p in (SKILL / "references").glob("*.md"))
        for nome in set(re.findall(r"/root/sheepringan/([a-z_]+\.(?:py|sh))", textos)):
            self.assertTrue((SCRIPTS / nome).exists(), nome)

    def test_readme_explica_o_nome_e_credita_o_openjutsu(self):
        r = (RAIZ / "README.md").read_text(encoding="utf-8")
        self.assertIn("sem ligação com Naruto", r)
        self.assertIn("o olho vermelho", r)
        self.assertIn("github.com/D3voz/openjutsu", r)
        self.assertIn("marcusforti/sheepringan/main/instalar.ps1", r)
        self.assertIn("marcusforti/sheepringan/main/instalar.sh", r)
        for nao_testado in ("Remover", "Não testado"):
            self.assertIn(nao_testado, r)

    def test_licencas_estao_no_pacote(self):
        t = (RAIZ / "THIRD-PARTY.md").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2026 D3voz", t)
        self.assertIn("MIT License", t)
        self.assertIn("MiniMax H3 Community License", t)
        self.assertIn("InsightFace", t)
        self.assertIn("Copyright (c) 2026 Marcus Forti", (RAIZ / "LICENSE").read_text(encoding="utf-8"))

    def test_medidas_traz_o_que_nao_foi_testado(self):
        m = (SKILL / "references" / "medidas.md").read_text(encoding="utf-8")
        for trecho in ("NÃO testado", "Remover", "Mac e Linux", "0,92", "0,68", "US$ 3,71", "US$ 0,14"):
            self.assertIn(trecho, m)


class TestScripts(unittest.TestCase):
    def test_todo_python_compila(self):
        for p in list(SCRIPTS.glob("*.py")) + list((RAIZ / "tests").glob("*.py")):
            py_compile.compile(str(p), doraise=True, cfile=str(Path(tempfile.gettempdir()) / "sheepringan-teste.pyc"))

    @unittest.skipUnless(bash_gnu(), "precisa de bash")
    def test_todo_shell_tem_sintaxe_valida(self):
        for p in list(SCRIPTS.glob("*.sh")) + [RAIZ / "instalar.sh"]:
            r = subprocess.run([bash_gnu(), "-n", p.as_posix()], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{p.name}: {r.stderr}")

    def test_sem_quebra_de_linha_do_windows_nos_scripts(self):
        for p in list(SCRIPTS.glob("*")) + [RAIZ / "instalar.sh"]:
            if p.is_file() and p.suffix in {".py", ".sh"}:
                self.assertNotIn(b"\r\n", p.read_bytes(), p.name)

    def test_scripts_da_maquina_nao_dependem_do_computador_local(self):
        for nome in ("objeto.py", "trocar_pessoa.py", "relay.py", "comfy_api.py"):
            texto = (SCRIPTS / nome).read_text(encoding="utf-8")
            self.assertNotRegex(texto, r"(?m)^\s*(import|from)\s+(requests|numpy|cv2|PIL)\b", nome)

    def test_chaves_da_vast_nunca_sao_impressas(self):
        texto = (SCRIPTS / "vast.py").read_text(encoding="utf-8")
        self.assertNotRegex(texto, r"print\([^)]*(api_key|private_key|\"email\"|'email')")


class TestInstaladorDaMaquina(unittest.TestCase):
    def sim(self, *args):
        return subprocess.run([bash_gnu(), (SCRIPTS / "instalar_maquina.sh").as_posix(), "--simular", *args], capture_output=True, text=True, timeout=120)

    @unittest.skipUnless(bash_gnu(), "precisa de bash")
    def test_simulacao_basica_termina_bem_e_baixa_so_os_sete_modelos(self):
        r = self.sim()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.strip().endswith("INSTALACAO_FIM"))
        self.assertEqual(r.stdout.count("+ baixar https://huggingface.co/"), 7)
        self.assertIn("[7/7]", r.stdout)
        self.assertNotIn("h3-relay", r.stdout)
        self.assertIn("torch==2.11.0", r.stdout)

    @unittest.skipUnless(bash_gnu(), "precisa de bash")
    def test_simulacao_relay_acrescenta_o_no_e_quatro_modelos(self):
        r = self.sim("--perfil", "relay")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.count("+ baixar https://huggingface.co/"), 11)
        self.assertIn("h3-relay", r.stdout)
        self.assertIn("[8/8]", r.stdout)
        self.assertIn("models/loras/h3-v2-challenge-eval-20261013/v2-1000.safetensors", r.stdout)

    @unittest.skipUnless(bash_gnu(), "precisa de bash")
    def test_perfil_invalido_e_recusado(self):
        r = self.sim("--perfil", "tudo")
        self.assertEqual(r.returncode, 2)

    def test_versoes_fixadas_tem_40_caracteres(self):
        texto = (SCRIPTS / "instalar_maquina.sh").read_text(encoding="utf-8")
        shas = re.findall(r"(?:_SHA=|\|)([0-9a-f]{40})\b", texto)
        self.assertEqual(len(shas), 8)  # ComfyUI, Openjutsu, 5 nos e o h3-relay

    def test_so_o_comfy_escuta_dentro_da_maquina(self):
        texto = (SCRIPTS / "instalar_maquina.sh").read_text(encoding="utf-8")
        self.assertIn("--listen 127.0.0.1", texto)
        self.assertNotIn("0.0.0.0", texto)

    def test_modelos_do_perfil_basico_cobrem_o_que_os_workflows_pedem(self):
        texto = (SCRIPTS / "instalar_maquina.sh").read_text(encoding="utf-8")
        for arq in ("minimax_h3_ref2va_pruned_int8_convrot", "qwen3vl_32b_minimax_h3_int4_convrot", "qwen3vl_8b_int8_convrot",
                    "minimax_h3_DMAD_4step_full_lora_avg_rank_39_bf16", "minimax_h3_video_vae_int8_convrot", "minimax_h3_audio_vae_fp32", "sam3.1_multiplex_fp16"):
            self.assertIn(arq, texto)


class TestInstaladoresDeUmaLinha(unittest.TestCase):
    def _conferir(self, home):
        for alvo in (".claude/skills", ".agents/skills"):
            raiz = home / alvo / "sheepringan"
            self.assertTrue((raiz / "SKILL.md").exists(), alvo)
            self.assertTrue((raiz / "scripts" / "objeto.py").exists(), alvo)
            self.assertTrue((raiz / "references" / "medidas.md").exists(), alvo)
            self.assertFalse(list(raiz.rglob("__pycache__")))
            self.assertFalse((home / alvo / "sheepringan.velho").exists())
            self.assertFalse((home / alvo / "sheepringan.novo").exists())

    @unittest.skipUnless(os.name == "nt" and shutil.which("pwsh"), "instalador do Windows")
    def test_windows_instala_e_reinstala(self):
        tmp = Path(tempfile.mkdtemp(prefix="srinst-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        env = {**os.environ, "USERPROFILE": str(tmp), "SHEEPRINGAN_ORIGEM": str(RAIZ), "TEMP": str(tmp)}
        for _ in range(2):
            r = subprocess.run(["pwsh", "-NoProfile", "-File", str(RAIZ / "instalar.ps1")], capture_output=True, text=True, env=env, timeout=180)
            self.assertIn("instalada", r.stdout, r.stdout + r.stderr)
            self.assertIn("/sheepringan", r.stdout)
        self._conferir(tmp)

    @unittest.skipUnless(bash_gnu(), "precisa de bash")
    def test_bash_instala_e_reinstala(self):
        tmp = Path(tempfile.mkdtemp(prefix="srinst-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        env = {**os.environ, "HOME": tmp.as_posix(), "SHEEPRINGAN_ORIGEM": RAIZ.as_posix()}
        for _ in range(2):
            r = subprocess.run([bash_gnu(), (RAIZ / "instalar.sh").as_posix()], capture_output=True, text=True, env=env, timeout=180)
            self.assertIn("instalada", r.stdout, r.stdout + r.stderr)
            self.assertIn("/sheepringan", r.stdout)
        self._conferir(tmp)


if __name__ == "__main__":
    unittest.main()
