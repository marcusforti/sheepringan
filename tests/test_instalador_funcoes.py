"""As funcoes de download do instalador da maquina (tamanho esperado, retomada, falha) contra um servidor local e um aria2c de mentira."""
import http.server
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

from ajudas import SCRIPTS, bash_gnu

ARIA_FALSO = """#!/bin/bash
echo x >> "$ARIA_LOG"
[ "$ARIA_MODO" = falha ] && exit 1
while [ $# -gt 0 ]; do
  case "$1" in
    -x|-s|-k) shift 2 ;;
    -d) D="$2"; shift 2 ;;
    -o) O="$2"; shift 2 ;;
    -*) shift ;;
    *) URL="$1"; shift ;;
  esac
done
curl -sL -o "$D/$O" "$URL"
"""


class Servidor:
    def __init__(self, arquivos, sem_tamanho=False):
        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _enviar(self, corpo_ou_none):
                dado = arquivos.get(self.path)
                if dado is None:
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                if not (sem_tamanho and self.command == "HEAD"):
                    self.send_header("Content-Length", str(len(dado)))
                self.end_headers()
                if self.command == "GET":
                    self.wfile.write(dado)

            do_GET = do_HEAD = lambda self: self._enviar(None)

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def fechar(self):
        self.srv.shutdown()
        self.srv.server_close()


@unittest.skipUnless(bash_gnu() and shutil.which("curl"), "precisa de bash e curl")
class TesteDownload(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="srdown-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        aria = self.bin / "aria2c"
        aria.write_text(ARIA_FALSO, encoding="utf-8", newline="\n")
        aria.chmod(0o755)
        self.log = self.tmp / "aria.log"
        self.log.write_text("")
        self.models = self.tmp / "models"

    def chamadas(self):
        return len(self.log.read_text().splitlines())

    def baixa(self, servidor, nome="m.safetensors", modo="ok"):
        script = (
            f'export SHEEPRINGAN_SO_FUNCOES=1; source "{(SCRIPTS / "instalar_maquina.sh").as_posix()}" --simular >/dev/null; '
            f'M="{self.models.as_posix()}"; baixa_um loras {nome} "{servidor.url}/{nome}"; echo "RC=$?"'
        )
        env = dict(os.environ, PATH=self.bin.as_posix() + os.pathsep + os.environ["PATH"], ARIA_LOG=str(self.log), ARIA_MODO=modo)
        r = subprocess.run([bash_gnu(), "-c", script], capture_output=True, text=True, env=env, timeout=120)
        return r.stdout

    def servir(self, dado, **kw):
        s = Servidor({"/m.safetensors": dado}, **kw)
        self.addCleanup(s.fechar)
        return s

    def test_baixa_confere_o_tamanho_e_nao_baixa_de_novo(self):
        dado = os.urandom(1_300_000)
        s = self.servir(dado)
        out = self.baixa(s)
        self.assertIn("BAIXOU m.safetensors", out)
        self.assertIn("RC=0", out)
        self.assertEqual((self.models / "loras" / "m.safetensors").read_bytes(), dado)
        self.assertEqual(self.chamadas(), 1)
        out = self.baixa(s)  # segunda vez: ja esta inteiro
        self.assertIn("RC=0", out)
        self.assertEqual(self.chamadas(), 1)

    def test_arquivo_pela_metade_e_completado(self):
        dado = os.urandom(1_300_000)
        s = self.servir(dado)
        (self.models / "loras").mkdir(parents=True)
        (self.models / "loras" / "m.safetensors").write_bytes(dado[:500_000])
        out = self.baixa(s)
        self.assertIn("RC=0", out)
        self.assertEqual((self.models / "loras" / "m.safetensors").read_bytes(), dado)
        self.assertEqual(self.chamadas(), 1)

    def test_falha_tenta_tres_vezes_e_avisa(self):
        s = self.servir(os.urandom(1_300_000))
        out = self.baixa(s, modo="falha")
        self.assertIn("FALHOU_DOWNLOAD", out)
        self.assertIn("RC=1", out)
        self.assertEqual(self.chamadas(), 3)

    def test_sem_tamanho_no_servidor_aceita_arquivo_grande_e_avisa(self):
        s = self.servir(os.urandom(1_300_000), sem_tamanho=True)
        out = self.baixa(s)
        self.assertIn("tamanho esperado nao confirmado", out)
        self.assertIn("RC=0", out)

    def test_arquivo_que_nao_existe_falha(self):
        s = self.servir(b"x" * 10)
        out = self.baixa(s, nome="outro.safetensors")
        self.assertIn("RC=1", out)


if __name__ == "__main__":
    unittest.main()
