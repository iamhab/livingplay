"""Prepara arquivos de apoio dos testes: copia os scripts do navegador e gera vídeos curtos de teste (webm)."""
import os, shutil, subprocess


def prepare(D):
    here = os.path.dirname(os.path.abspath(__file__))
    for n in ("pw_page.py", "pw_remote.py"):
        shutil.copy(os.path.join(here, n), os.path.join(D, n))
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    for name, secs in (("clip8.webm", 8), ("clip3.webm", 3)):
        out = os.path.join(D, name)
        if not os.path.exists(out):
            subprocess.run([ff, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=15",
                            "-f", "lavfi", "-i", "sine=frequency=440", "-t", str(secs), "-c:v", "libvpx",
                            "-b:v", "300k", "-c:a", "libvorbis", out], check=True)
