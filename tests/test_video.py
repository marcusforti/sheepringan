"""preparar_video.py e montar.py com videos sinteticos (precisa do ffmpeg)."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from ajudas import rodar

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def ff(*args):
    r = subprocess.run([FFMPEG, "-v", "error", "-y", *map(str, args)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def sonda(arq):
    r = subprocess.run([FFPROBE, "-v", "error", "-count_frames", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate,duration,nb_read_frames",
                        "-of", "json", str(arq)], capture_output=True, text=True)
    d = json.loads(r.stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    return {"quadros": int(v["nb_read_frames"]), "fps": v["r_frame_rate"], "w": int(v["width"]), "h": int(v["height"]),
            "dur_audio": float(a["duration"]) if a else None, "dur_video": float(v["duration"]), "dur": float(d["format"]["duration"])}


def cor_em(arq, t):
    """Cor media (R, G, B) do quadro no instante t."""
    r = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{t:.3f}", "-i", str(arq), "-frames:v", "1", "-vf", "scale=4:4", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                       capture_output=True)
    b = r.stdout
    n = len(b) // 3
    return tuple(sum(b[i::3]) / n for i in range(3))


@unittest.skipUnless(FFMPEG and FFPROBE, "precisa do ffmpeg")
class TesteVideo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="sheepringan-video-"))
        # celular: 30 quadros, vertical grande, audio MENOR que o video (o caso que quebrava a montagem)
        ff("-f", "lavfi", "-i", "testsrc2=size=540x960:rate=30:duration=8", "-f", "lavfi", "-i", "sine=frequency=440:duration=7.9:sample_rate=44100",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", cls.tmp / "celular.mp4")
        ff("-f", "lavfi", "-i", "testsrc2=size=540x960:rate=30:duration=8", "-c:v", "libx264", "-pix_fmt", "yuv420p", cls.tmp / "mudo.mp4")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, True)

    def prep(self, entrada, *args):
        saida = self.tmp / "prep.mp4"
        if saida.exists():
            saida.unlink()
        r = rodar("preparar_video.py", self.tmp / entrada, "-o", saida, *args)
        return r, saida

    def test_73_quadros_a_24_fps_com_audio_maior_que_o_video(self):
        r, saida = self.prep("celular.mp4", "--inicio", "1", "--quadros", "73")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        s = sonda(saida)
        self.assertEqual((s["quadros"], s["fps"]), (73, "24/1"))
        self.assertGreaterEqual(s["dur_audio"], 73 / 24)
        self.assertLessEqual(min(s["w"], s["h"]), 720)
        self.assertIn("--clip 3.062", r.stdout)

    def test_video_sem_audio_ganha_silencio_do_tamanho_certo(self):
        r, saida = self.prep("mudo.mp4", "--quadros", "56")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("nao tem audio", r.stdout)
        s = sonda(saida)
        self.assertEqual(s["quadros"], 56)
        self.assertGreaterEqual(s["dur_audio"], 56 / 24)

    def test_duracao_escolhe_o_maior_numero_valido_que_cabe(self):
        r, saida = self.prep("celular.mp4", "--duracao", "3")  # 72 quadros pedidos -> 56 (17x3+5)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(sonda(saida)["quadros"], 56)

    def test_sem_pedido_usa_no_maximo_158_quadros(self):
        r, saida = self.prep("celular.mp4")
        self.assertEqual(sonda(saida)["quadros"], 158)

    def test_quadros_invalidos_sao_recusados_com_a_lista_certa(self):
        r, _ = self.prep("celular.mp4", "--quadros", "60")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("17 x k + 5", r.stderr)
        self.assertIn("158", r.stderr)

    def test_pedir_mais_do_que_o_video_tem_e_recusado(self):
        r, _ = self.prep("celular.mp4", "--inicio", "7", "--quadros", "73")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("so tem", r.stderr)

    # ---- montar
    def test_montar_troca_de_trecho_com_flash_e_audio_do_original(self):
        t = self.tmp
        ff("-f", "lavfi", "-i", "color=c=red:size=720x1280:rate=30:duration=8", "-f", "lavfi", "-i", "sine=frequency=440:duration=8", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", t / "orig.mp4")
        ff("-f", "lavfi", "-i", "color=c=green:size=736x1312:rate=24:duration=4", "-c:v", "libx264", "-pix_fmt", "yuv420p", t / "a.mp4")
        ff("-f", "lavfi", "-i", "color=c=blue:size=736x1312:rate=24:duration=3", "-c:v", "libx264", "-pix_fmt", "yuv420p", t / "b.mp4")
        saida = t / "final.mp4"
        r = rodar("montar.py", "--original", t / "orig.mp4", "--saida", saida, "--parte", f"{t / 'a.mp4'}@2", "--parte", f"{t / 'b.mp4'}@5", "--corte", "3", "--corte", "6")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        s = sonda(saida)
        self.assertAlmostEqual(s["dur"], 8.0, delta=0.2)
        self.assertEqual((s["w"], s["h"]), (720, 1280))  # no tamanho do original
        self.assertIsNotNone(s["dur_audio"])
        verm, verde, azul = cor_em(saida, 1.0), cor_em(saida, 4.5), cor_em(saida, 7.0)
        self.assertGreater(verm[0], verm[1] + 80)
        self.assertGreater(verde[1], verde[0] + 80)
        self.assertGreater(azul[2], azul[0] + 80)
        # flash branco logo antes e depois do corte
        self.assertGreater(min(cor_em(saida, 2.99)), 200)
        self.assertGreater(min(cor_em(saida, 3.02)), 120)

    def test_montar_recusa_corte_fora_do_que_a_parte_cobre(self):
        t = self.tmp
        ff("-f", "lavfi", "-i", "color=c=red:size=320x240:rate=30:duration=4", "-c:v", "libx264", "-pix_fmt", "yuv420p", t / "o2.mp4")
        ff("-f", "lavfi", "-i", "color=c=green:size=320x240:rate=24:duration=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", t / "p2.mp4")
        r = rodar("montar.py", "--original", t / "o2.mp4", "--saida", t / "x.mp4", "--parte", f"{t / 'p2.mp4'}@2", "--corte", "1.0")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cobre de", r.stderr)

    def test_montar_exige_um_corte_por_parte(self):
        r = rodar("montar.py", "--original", "a.mp4", "--saida", "b.mp4", "--parte", "x.mp4@1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("um --corte para cada --parte", r.stderr)


if __name__ == "__main__":
    unittest.main()
