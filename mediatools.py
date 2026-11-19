# -*- coding: utf-8 -*-
"""Ferramentas de mídia: legendas (arquivo ao lado, embutida ou do YouTube), volume uniforme e leitura do codec."""
import glob
import hashlib
import os
import re
import subprocess

NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
LANG_TOKENS = {"pt": {"pt", "por", "ptbr", "pt-br", "br", "portuguese", "português", "portugues"},
               "en": {"en", "eng", "en-us", "en-gb", "english", "inglês", "ingles"}}
YT_LANGS = {"pt": ["pt", "pt-BR", "pt-PT"], "en": ["en", "en-US", "en-GB"]}
CAST_LANG = {"pt": "pt-BR", "en": "en-US"}
TEXT_SUBS = {"subrip", "ass", "ssa", "mov_text", "webvtt", "text", "srt"}


def _read(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", "replace")


def srt_to_vtt(text):
    """Converte SRT (ou ajusta um VTT) para WebVTT, o formato que o Chromecast entende."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿")
    out = []
    for ln in text.split("\n"):
        if "-->" in ln:
            ln = re.sub(r"(\d{1,2}:\d{2}:\d{2}),(\d{1,3})", r"\1.\2", ln)
            ln = re.sub(r"(^|\s)(\d{2}:\d{2}),(\d{3})", r"\1\2.\3", ln)
        ln = re.sub(r"</?font[^>]*>", "", ln)
        ln = re.sub(r"\{\\[^}]*\}", "", ln)  # marcações de posição do ASS
        out.append(ln)
    body = "\n".join(out).strip()
    if not body.startswith("WEBVTT"):
        body = "WEBVTT\n\n" + body
    return body + "\n"


def _tokens(name):
    return {t for t in re.split(r"[\s._\-\[\]()]+", name.lower()) if t}


def find_external(path, lang):
    """Legenda .srt/.vtt com o mesmo nome do vídeo (aceita sufixos de idioma: filme.pt.srt, filme.por.srt)."""
    d, base = os.path.dirname(path), os.path.splitext(os.path.basename(path))[0].lower()
    cands = []
    try:
        for n in os.listdir(d or "."):
            low = n.lower()
            if low.endswith((".srt", ".vtt")) and low.startswith(base):
                cands.append(n)
    except OSError:
        return None
    if not cands:
        return None
    want = LANG_TOKENS.get(lang, set())

    def score(n):
        rest = os.path.splitext(n)[0][len(base):]
        tk = _tokens(rest)
        s = 0
        if tk & want:
            s += 10
        if not tk:
            s += 3  # sem sufixo: legenda "padrão" do vídeo
        return (-s, n)
    best = sorted(cands, key=score)[0]
    return os.path.join(d, best)


def _out_path(cache, key, lang):
    d = os.path.join(cache, "subs")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{key}.{lang}.vtt")


def _embedded(ffmpeg, path, lang, out):
    """Extrai a legenda de texto embutida (mkv, mp4...) que melhor combina com o idioma."""
    try:
        err = subprocess.run([ffmpeg, "-nostdin", "-hide_banner", "-i", path], capture_output=True, text=True,
                             creationflags=NOWIN, timeout=60).stderr
    except Exception:
        return False
    subs = [(int(m.group(1)), (m.group(2) or "").lower()) for m in
            re.finditer(r"Stream #0:(\d+)(?:\((\w+)\))?[^\n]*Subtitle: (\w+)", err) if m.group(3).lower() in TEXT_SUBS]
    if not subs:
        return False
    want = LANG_TOKENS.get(lang, set())
    idx = next((i for i, lg in subs if lg in want), subs[0][0])
    tmp = out + ".part.vtt"
    try:
        r = subprocess.run([ffmpeg, "-nostdin", "-loglevel", "error", "-y", "-i", path, "-map", f"0:{idx}",
                            "-c:s", "webvtt", tmp], capture_output=True, text=True, creationflags=NOWIN, timeout=180)
        ok = r.returncode == 0 and os.path.isfile(tmp) and os.path.getsize(tmp) > 20
        if ok:
            os.replace(tmp, out)
        return ok
    finally:
        if os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def local_vtt(path, lang, cache, ffmpeg=None):
    """Legenda (WebVTT) de um arquivo do computador, ou None se não houver."""
    if lang not in LANG_TOKENS or not os.path.isfile(path):
        return None
    ext = find_external(path, lang)
    st = os.stat(path)
    key = hashlib.sha1(f"{path}|{st.st_mtime}|{st.st_size}|{ext}|{os.path.getmtime(ext) if ext else 0}".encode(),
                       usedforsecurity=False).hexdigest()[:14]
    out = _out_path(cache, key, lang)
    if os.path.isfile(out):
        return out
    if ext:
        with open(out, "w", encoding="utf-8") as f:
            f.write(srt_to_vtt(_read(ext)))
        return out
    if ffmpeg and _embedded(ffmpeg, path, lang, out):
        return out
    return None


def youtube_vtt(url, vid, lang, cache, base_opts):
    """Legenda do YouTube (a do autor ou, se não houver, a automática), baixada uma vez e guardada."""
    if lang not in YT_LANGS or not vid:
        return None
    d = os.path.join(cache, "subs")
    os.makedirs(d, exist_ok=True)
    none = os.path.join(d, f"{vid}.{lang}.none")
    if os.path.isfile(none):
        return None
    pick = lambda: next(iter(sorted(glob.glob(os.path.join(glob.escape(d), glob.escape(vid) + ".*.vtt")),
                                    key=lambda p: (".orig" in p, len(p)))), None)
    got = pick()
    if got:
        return got
    import yt_dlp
    opts = dict(base_opts)
    opts.update(skip_download=True, writesubtitles=True, writeautomaticsub=True, subtitleslangs=YT_LANGS[lang],
                subtitlesformat="vtt", noplaylist=True, outtmpl=os.path.join(d, "%(id)s.%(ext)s"))
    with yt_dlp.YoutubeDL(opts) as y:
        y.extract_info(url, download=True)
    got = pick()
    if not got:
        open(none, "w").close()
    return got


def video_codec(ffmpeg, path):
    """Codec do vídeo ('h264', 'hevc'...) lido do arquivo, ou None."""
    try:
        err = subprocess.run([ffmpeg, "-nostdin", "-hide_banner", "-i", path], capture_output=True, text=True,
                             creationflags=NOWIN, timeout=60).stderr
    except Exception:
        return None
    m = re.search(r"Video: (\w+)", err)
    return m.group(1).lower() if m else None


LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"


def normalize(ffmpeg, path, timeout=1800):
    """Deixa o volume do arquivo (mp4/m4a) num nível uniforme; o vídeo é só copiado, então é rápido."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".mp4", ".m4v", ".m4a") or not os.path.isfile(path):
        return False
    tmp = path + ".norm" + ext
    cmd = [ffmpeg, "-nostdin", "-loglevel", "error", "-y", "-i", path]
    cmd += ["-vn"] if ext == ".m4a" else ["-map", "0:v?", "-c:v", "copy"]
    cmd += ["-map", "0:a:0?", "-af", LOUDNORM, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, creationflags=NOWIN, timeout=timeout)
        if r.returncode == 0 and os.path.isfile(tmp) and os.path.getsize(tmp) > 1024:
            os.replace(tmp, path)
            return True
    except Exception:
        pass
    finally:
        if os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
    return False
