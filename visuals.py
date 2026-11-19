# -*- coding: utf-8 -*-
"""Telas da TV para o modo áudio: "Capa" (imagem elegante com o título e o artista).

Tudo é gerado localmente: o Pillow desenha a cena e o ffmpeg junta imagem + música em um arquivo de vídeo comum,
que o programa envia à TV como qualquer outro vídeo. Assim a tela inteira é do Livingplay (nome, título, artista)."""
import hashlib
import io
import os
import re
import subprocess
import threading
import time

from PIL import Image, ImageDraw, ImageFilter, ImageFont

Image.MAX_IMAGE_PIXELS = 40_000_000  # imagem gigante (capa mal feita ou maliciosa) é recusada em vez de travar o PC

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "assets", "fonts")
VERSION = 4  # aumente quando o desenho mudar: as cenas antigas do cache deixam de ser usadas
NOWIN = 0x08000000 if os.name == "nt" else 0
LAST_ERR = [""]  # última mensagem de erro do ffmpeg (para o registro de diagnóstico)

# (fundo escuro, fundo claro, cor dos gráficos): paletas sóbrias; cada música usa uma, sempre a mesma
PALETTES = [
    ("#08142e", "#1b3fa8", "#8fb4ff"),   # azul Livingplay
    ("#1b0d2b", "#612a78", "#e0b0ff"),   # ameixa
    ("#052428", "#0f6e66", "#86eadb"),   # verde-água
    ("#1d1230", "#a6405f", "#ffbfae"),   # entardecer
    ("#0f1033", "#3d34b8", "#b3bcff"),   # índigo
    ("#0b2015", "#2b7449", "#a4ecbc"),   # floresta
    ("#15151a", "#3c3c48", "#f0d595"),   # grafite e ouro
    ("#071a2b", "#136a9a", "#9fe0ff"),   # mar
]


def pick_palette(seed):
    h = int(hashlib.sha1(seed.encode("utf-8", "ignore"), usedforsecurity=False).hexdigest()[:8], 16)
    return PALETTES[h % len(PALETTES)]


def _rgb(c):
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _font(bold, size):
    """Mesma fonte do programa (DejaVu Sans Mono), para a tela da TV combinar com o app."""
    name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    try:
        return ImageFont.truetype(os.path.join(FONTS, name), size)
    except Exception:
        return ImageFont.load_default()


def _mono(size):
    try:
        return ImageFont.truetype(os.path.join(FONTS, "DejaVuSansMono-Bold.ttf"), size)
    except Exception:
        return ImageFont.load_default()


def _wrap(draw, text, font, width, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textlength(last + "…", font=font) > width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines


def _gradient(W, H, c1, c2):
    """Degradê diagonal suave (do escuro, no canto de cima, ao mais claro, embaixo à direita)."""
    a, b = _rgb(c1), _rgb(c2)
    small = Image.new("RGB", (64, 36))
    px = small.load()
    for y in range(36):
        for x in range(64):
            t = (x / 63 * .45 + y / 35 * .55) ** 1.35
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return small.resize((W, H), Image.BICUBIC)


def _glow(base, cx, cy, r, color, alpha):
    """Mancha de luz macia (círculo borrado) para dar profundidade ao fundo."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse((cx - r, cy - r, cx + r, cy + r), fill=_rgb(color) + (int(255 * alpha),))
    layer = layer.filter(ImageFilter.GaussianBlur(r * .55))
    base.alpha_composite(layer)


def _round_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius, fill=255)
    return m


def _square(img, n):
    img = img.convert("RGB")
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    return img.resize((n, n), Image.LANCZOS)


def scene(W, H, title, artist, brand, kicker, art=None, bars=False, seed=None):
    """Desenha a cena. Com bars=True deixa o terço de baixo livre para os gráficos animados."""
    c1, c2, accent = pick_palette(seed or (title + artist))
    img = _gradient(W, H, c1, c2).convert("RGBA")
    if art is not None:  # fundo com a própria capa, bem borrada e escurecida
        bg = _fit(art, W // 8, H // 8).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(W // 38)).convert("RGBA")
        veil = Image.new("RGBA", (W, H), _rgb(c1) + (178,))
        bg.alpha_composite(veil)
        img = Image.blend(img, bg, .85)
    _glow(img, int(W * .18), int(H * .2), int(H * .55), accent, .16)
    _glow(img, int(W * .88), int(H * .92), int(H * .62), c2, .45)
    d = ImageDraw.Draw(img)
    u = H / 1080.0
    area_h = int(H * (.60 if bars else 1.0))
    # ---- capa: o cartão segue a proporção REAL da imagem (horizontal, quadrada ou vertical), sem cortar nem esticar
    cw = ch = 0
    sharp = False
    if art is not None:
        asp = art.width / max(1, art.height)
        asp = min(2.2, max(0.45, asp))
        maxw, maxh = int(W * .36), int(area_h * .74)
        if asp >= maxw / maxh:
            cw, ch = maxw, int(maxw / asp)
        else:
            cw, ch = int(maxh * asp), maxh
        sharp = art.width >= cw * .75 and art.height >= ch * .75 and min(art.size) >= 240
    ax, ay = int(W * .09), (area_h - ch) // 2 - int(14 * u)
    if sharp:
        rad = int(22 * u)
        pic = _fit(art, cw, ch).convert("RGBA")
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle((ax, ay + int(20 * u), ax + cw, ay + ch + int(20 * u)), rad, fill=(0, 0, 0, 135))
        img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(int(30 * u))))
        img.paste(pic, (ax, ay), _round_mask((cw, ch), rad))
        edge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(edge).rounded_rectangle((ax, ay, ax + cw - 1, ay + ch - 1), rad, outline=(255, 255, 255, 46), width=max(1, int(2 * u)))
        img.alpha_composite(edge)
        tx = ax + cw + int(W * .05)
    else:
        # sem capa nítida: anéis finos e quase invisíveis ao fundo, sem desenhar nenhum ícone
        ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rd = ImageDraw.Draw(ring)
        cx, cy = int(W * .84), int(area_h * .5)
        for k, r in enumerate((.20, .31, .43)):
            rr = int(H * r)
            rd.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=_rgb(accent) + (34 - k * 8,), width=max(2, int(3 * u)))
        img.alpha_composite(ring)
        tx = ax
    side = ch
    tw = W - tx - int(W * .07)
    d = ImageDraw.Draw(img)
    f_k = _mono(int(24 * u))
    fs = int(64 * u)
    while True:
        f_t = _font(True, fs)
        lines = _wrap(d, title or brand, f_t, tw, 3)
        if len(lines) <= 2 or fs <= int(36 * u):
            break
        fs -= int(4 * u)
    f_a = _font(False, int(34 * u))
    alines = _wrap(d, artist, f_a, tw, 1) if artist else []
    block = int(58 * u) + int(len(lines) * fs * 1.22) + (int(14 * u) + int(46 * u) if alines else 0)
    ky = ay + max(0, (side - block) // 2) if sharp else max(int(40 * u), (area_h - block) // 2)
    d.text((tx, ky), "  ".join(kicker.upper()), font=f_k, fill=_rgb(accent) + (235,))
    y = ky + int(58 * u)
    for ln in lines:
        d.text((tx, y), ln, font=f_t, fill=(255, 255, 255, 255))
        y += int(fs * 1.22)
    if alines:
        y += int(14 * u)
        d.text((tx, y), alines[0], font=f_a, fill=(255, 255, 255, 190))
    # ---- assinatura do programa, discreta, no canto de baixo
    f_b = _mono(int(26 * u))
    bx, by = int(W * .09), H - int(78 * u)
    try:
        mini = Image.open(os.path.join(HERE, "assets", "icon_master.png")).convert("RGBA").resize((int(40 * u),) * 2, Image.LANCZOS)
        img.alpha_composite(mini, (bx, by - int(6 * u)))
        bx += int(56 * u)
    except Exception:
        pass
    d.text((bx, by), brand, font=f_b, fill=(255, 255, 255, 210))
    return img.convert("RGB"), accent


def _get_image(url, limit=6_000_000):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "Livingplay"})
    with urllib.request.urlopen(req, timeout=8) as r:
        data = r.read(limit + 1)
    if len(data) > limit:
        return None
    return Image.open(io.BytesIO(data))


def fetch_art(url):
    """Baixa a miniatura do vídeo (só https, com limite de tamanho), procurando a versão de maior resolução."""
    if not url or not str(url).startswith("https://"):
        return None
    best = None
    cands = [url]
    m = re.search(r"^(https://[^/]+)/vi(?:_webp)?/([\w-]{11})/", str(url))
    if m:  # miniaturas desse tipo existem em várias resoluções: tenta as maiores antes
        cands = [f"{m.group(1)}/vi/{m.group(2)}/maxresdefault.jpg", f"{m.group(1)}/vi/{m.group(2)}/sddefault.jpg", url]
    for u in cands:
        try:
            im = _get_image(u)
        except Exception:
            continue
        if im is not None and (best is None or im.width > best.width):
            best = im
        if best is not None and best.width >= 1000:
            break
    return best


def _trim_bars(img):
    """Tira as faixas pretas (em cima/embaixo ou dos lados) que algumas miniaturas trazem, para mostrar só a imagem real."""
    try:
        g = img.convert("L")
        w, h = g.size

        def dark_row(y):
            return g.crop((0, y, w, y + 1)).getextrema()[1] < 30

        def dark_col(x):
            return g.crop((x, 0, x + 1, h)).getextrema()[1] < 30
        top, bot, lef, rig = 0, h - 1, 0, w - 1
        while top < h // 3 and dark_row(top):
            top += 1
        while bot > h - h // 3 and dark_row(bot):
            bot -= 1
        while lef < w // 3 and dark_col(lef):
            lef += 1
        while rig > w - w // 3 and dark_col(rig):
            rig -= 1
        if (top > 2 or bot < h - 3 or lef > 2 or rig < w - 3) and (rig - lef) > w * .3 and (bot - top) > h * .3:
            m = max(3, int(min(w, h) * .012))  # margem de segurança: some o contorno suave que sobra na emenda da faixa preta
            return img.crop((lef + (m if lef > 2 else 0), top + (m if top > 2 else 0),
                             rig + 1 - (m if rig < w - 3 else 0), bot + 1 - (m if bot < h - 3 else 0)))
    except Exception:
        pass
    return img


def _fit(img, w, h):
    """Preenche w x h cortando o excesso no centro, reduzindo com qualidade e realçando de leve a nitidez."""
    img = img.convert("RGB")
    sw, sh = img.size
    k = max(w / sw, h / sh)
    nw, nh = max(w, round(sw * k)), max(h, round(sh * k))
    img = img.resize((nw, nh), Image.LANCZOS)
    img = img.crop(((nw - w) // 2, (nh - h) // 2, (nw - w) // 2 + w, (nh - h) // 2 + h))
    if k < 1:
        img = img.filter(ImageFilter.UnsharpMask(radius=1.1, percent=55, threshold=2))
    return img


def embedded_art(path):
    """Capa embutida no arquivo de áudio (mp3, m4a, flac), se houver."""
    try:
        import mutagen
        f = mutagen.File(path)
        if f is None:
            return None
        data = None
        tags = getattr(f, "tags", None)
        if tags is not None:
            for k in tags.keys():
                if str(k).startswith("APIC"):
                    data = tags[k].data
                    break
            if data is None and "covr" in tags:
                data = bytes(tags["covr"][0])
        if data is None and getattr(f, "pictures", None):
            data = f.pictures[0].data
        return Image.open(io.BytesIO(data)) if data else None
    except Exception:
        return None


def tags_of(path):
    """(título, artista) gravados no arquivo de áudio, se houver."""
    try:
        import mutagen
        f = mutagen.File(path, easy=True)
        if f is None or not f.tags:
            return "", ""
        g = lambda k: (f.tags.get(k) or [""])[0]
        return g("title"), g("artist")
    except Exception:
        return "", ""


def key_for(audio_path, style):
    try:
        st = os.stat(audio_path)
        raw = f"{os.path.abspath(audio_path)}|{st.st_size}|{int(st.st_mtime)}|{style}|{VERSION}"
    except OSError:
        raw = f"{audio_path}|{style}|{VERSION}"
    return hashlib.sha1(raw.encode("utf-8", "ignore"), usedforsecurity=False).hexdigest()[:16]


def _probe_audio(ffmpeg, path):
    p = subprocess.run([ffmpeg, "-hide_banner", "-i", path], capture_output=True, text=True, creationflags=NOWIN).stderr
    m = re.search(r"Audio: (\w+)", p)
    d = re.search(r"Duration: (\d+):(\d+):(\d+\.?\d*)", p)
    secs = int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3)) if d else 0.0
    return (m.group(1) if m else ""), secs


def build(ffmpeg, audio_path, out_path, style, title, artist, brand, kicker, art_url=None, progress=None,
          cancelled=lambda: False, timeout=None):
    """Cria o vídeo da tela (style = 'cover'). Devolve True se deu certo."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    art = embedded_art(audio_path) or fetch_art(art_url)
    if art is not None:
        art = _trim_bars(art)
    W, H = 1920, 1080
    img, accent = scene(W, H, title, artist, brand, kicker, art=art, bars=False, seed=f"{title}|{artist}")
    png = out_path + ".scene.png"
    img.save(png)
    codec, secs = _probe_audio(ffmpeg, audio_path)
    acodec = ["-c:a", "copy"] if codec in ("aac", "mp3") else ["-c:a", "aac", "-b:a", "192k"]
    tmp = out_path + ".part.mp4"
    cmd = [ffmpeg, "-loglevel", "error", "-y", "-loop", "1", "-framerate", "10", "-i", png, "-i", audio_path,
           "-map", "0:v", "-map", "1:a:0", "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast",
           "-crf", "26", "-r", "10", "-g", "20", "-pix_fmt", "yuv420p"] + acodec + (
           ["-t", f"{secs:.2f}"] if secs else ["-shortest"]) + [
           "-progress", "pipe:1", "-nostats", "-movflags", "+faststart", tmp]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=NOWIN)
    err = []
    threading.Thread(target=lambda: err.append(proc.stderr.read()), daemon=True).start()
    t0 = time.time()
    try:
        for line in proc.stdout:
            if cancelled() or (timeout and time.time() - t0 > timeout):
                proc.kill()
                break
            if line.startswith("out_time_us=") and progress and secs:
                try:
                    progress(min(99, int(int(line.split("=")[1]) / 1e6 * 100 / secs)))
                except ValueError:
                    pass
    finally:
        proc.wait()
        try:
            os.remove(png)
        except OSError:
            pass
    LAST_ERR[0] = (err[0] if err else "")[-400:]
    if proc.returncode != 0 or not os.path.isfile(tmp) or os.path.getsize(tmp) < 2048:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False
    os.replace(tmp, out_path)
    return True
