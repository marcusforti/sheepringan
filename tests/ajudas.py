"""Ajudas dos testes: caminhos e um jeito de rodar os scripts da skill como o agente roda."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ / "skill" / "sheepringan" / "scripts"
TESTES = Path(__file__).resolve().parent


def rodar(script, *args, env=None, cwd=None, timeout=120):
    e = dict(os.environ, PYTHONUTF8="1")
    e.update(env or {})
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=e, cwd=cwd, timeout=timeout)


def bash_gnu():
    """Acha um bash de verdade (no Windows, o do Git). Devolve None se nao houver."""
    b = shutil.which("bash")
    if not b:
        return None
    r = subprocess.run([b, "--version"], capture_output=True, text=True)
    return b if r.returncode == 0 and "GNU bash" in r.stdout else None


class Casa(unittest.TestCase):
    """Uma pasta temporaria para ser a casa do usuario (~/.sheepringan) e o 'computador remoto'."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sheepringan-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.casa = self.tmp / "casa"
        self.remota = self.tmp / "remota"
        self.casa.mkdir()
        self.remota.mkdir()

    def env_base(self):
        return {"SHEEPRINGAN_HOME": str(self.casa), "SHEEPRINGAN_RAIZ_REMOTA": self.remota.as_posix()}

    def gravar_maquina(self, **extra):
        d = {"id": 777, "host": "127.0.0.1", "port": 2222, "usuario": "root", "chave": str(self.tmp / "chave-que-nao-existe")}
        d.update(extra)
        (self.casa / "maquina.json").write_text(json.dumps(d), encoding="utf-8")
