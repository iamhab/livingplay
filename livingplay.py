"""Livingplay - player e cache local para mídia na TV (compatível com Chromecast) ou no computador, com fila, linha do tempo e controle pelo celular."""
import hashlib, hmac, json, os, queue, random, re, secrets, subprocess, sys, threading, time, traceback, urllib.parse
# Versão instalada: o Python vem junto com o programa; diz ao Tk onde ficam as suas bibliotecas.
_RT = os.path.dirname(os.path.abspath(sys.executable))
for _n, _d in (("TCL_LIBRARY", "tcl8.6"), ("TK_LIBRARY", "tk8.6")):
    if os.path.isdir(os.path.join(_RT, "tcl", _d)):
        os.environ[_n] = os.path.join(_RT, "tcl", _d)
import tkinter as tk
from tkinter import ttk, filedialog
from app_info import APP_NAME, APP_SLUG, TERMS_VERSION
try:
    import visuals  # tela Capa (precisa do Pillow); sem ele o áudio toca como antes
except Exception:
    visuals = None
from i18n import T, LANGS, LANG, detect_lang, set_lang
import winframe
import dialogs
import mediatools
from ui_widgets import ScrollBox, UI, Btn, Segmented, Pill, Logo, draw_icon, rrect, oval, Chevron, hide_title_icon
from pc_player import PCDevice, pc_html
from remote_page import REMOTE_HTML
from tutorial import Tutorial
from terms import TermsGate, NoticeDialog

HOME = os.path.expanduser("~")
CFG = os.path.join(HOME, "." + APP_SLUG + ".json")
LOG = os.path.join(HOME, "." + APP_SLUG + ".log")
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
CFGS = {"cache": os.path.join(HOME, APP_NAME + "Cache"), "max_gb": 3.0,
        "cookies_file": False, "mode": "video", "gap": 4.0, "quality": "auto", "screen": "cover",
        "subs": "off", "norm": False, "hevc": False}
UPDATED = {"done": False}
PACE = {"t": 0.0}
BOT = "Sign in to confirm"
BAD_PREFIX = ("Não consegui", "Parei", "Erro", "ERRO", "O YouTube bloqueou", "Could not", "Stopped", "Error",
              "YouTube blocked", "Unexpected")
DIRECT = {".mp4": "video/mp4", ".m4v": "video/mp4", ".webm": "video/webm", ".mp3": "audio/mpeg",
          ".m4a": "audio/mp4", ".aac": "audio/aac", ".wav": "audio/wav", ".flac": "audio/flac",
          ".ogg": "audio/ogg", ".opus": "audio/ogg"}


class Blocked(Exception):
    pass


def log(text):
    try:
        if os.path.getsize(LOG) > 1_000_000:  # o registro nunca passa de ~1 MB (guarda só a versão anterior)
            os.replace(LOG, LOG + ".old")
    except OSError:
        pass
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S ") + str(text) + "\n")
    except Exception:
        pass


_CFG_LOCK = threading.RLock()


def _item_ok(t):
    return (isinstance(t, dict) and isinstance(t.get("title", ""), str)
            and (isinstance(t.get("url"), str) or isinstance(t.get("path"), str)))


def sanitize_cfg(d):
    """Confere tipo e faixa de cada ajuste. Valor estranho (arquivo editado à mão, backup de outra versão,
    disco com defeito) é descartado e o programa usa o padrão, em vez de travar ao abrir."""
    if not isinstance(d, dict):
        return {}
    out = dict(d)
    rules = {
        "lang": lambda v: isinstance(v, str) and len(v) <= 10,
        "theme": lambda v: isinstance(v, str),
        "size": lambda v: isinstance(v, str),
        "mode": lambda v: v in ("video", "audio"),
        "quality": lambda v: isinstance(v, str) and len(v) <= 10,
        "subs": lambda v: v in ("off", "pt", "en"),
        "target": lambda v: v in ("cast", "pc"),
        "cache": lambda v: isinstance(v, str) and 0 < len(v) < 260,
        "token": lambda v: isinstance(v, str) and 20 <= len(v) <= 100,
        "ip": lambda v: isinstance(v, str) and len(v) <= 64,
        "fold": lambda v: isinstance(v, dict),
        "files_ui": lambda v: isinstance(v, dict),
        "session": lambda v: isinstance(v, dict) and isinstance(v.get("tracks", []), list),
    }
    for k, ok in rules.items():
        if k in out and not ok(out[k]):
            out.pop(k)
    for k, lo, hi in (("max_gb", 0.0, 100000.0), ("adjust", -10.0, 10.0), ("lookahead", 1, 20)):
        if k in out:
            try:
                v = float(out[k])
                if v != v or not lo <= v <= hi:
                    raise ValueError
                out[k] = int(v) if k == "lookahead" else v
            except (TypeError, ValueError):
                out.pop(k)
    for k in ("norm", "hevc", "cookies_file", "native_frame", "terms_ok"):
        if k in out and not isinstance(out[k], (bool, int)):
            out.pop(k)
    pls = out.get("playlists")
    if pls is not None:
        if isinstance(pls, dict):
            out["playlists"] = {str(n)[:200]: [t for t in v if _item_ok(t)]
                                for n, v in pls.items() if isinstance(v, list)}
        else:
            out.pop("playlists")
    if "session" in out:
        out["session"]["tracks"] = [t for t in out["session"].get("tracks", []) if _item_ok(t)]
        try:
            out["session"]["idx"] = max(0, int(out["session"].get("idx", 0)))
            out["session"]["pos"] = max(0, int(float(out["session"].get("pos", 0))))
        except (TypeError, ValueError):
            out.pop("session")
    return out


def load_cfg():
    try:
        with open(CFG, encoding="utf-8") as f:
            d = json.load(f)
        return sanitize_cfg(d)
    except FileNotFoundError:
        return {}
    except Exception:
        log("configuração ilegível:\n" + traceback.format_exc())
        try:  # guarda uma cópia do arquivo ruim em vez de perder tudo em silêncio
            os.replace(CFG, CFG + ".corrompido")
        except OSError:
            pass
        return {}


def save_cfg(d):
    """Grava por inteiro ou não grava: escreve num arquivo temporário e troca (sem arquivo pela metade)."""
    with _CFG_LOCK:
        try:
            for _ in range(3):
                try:
                    data = json.dumps(d, ensure_ascii=False)
                    break
                except RuntimeError:  # outra thread mexeu na configuração durante a leitura
                    time.sleep(0.05)
            else:
                return
            tmp = CFG + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(data)
            os.replace(tmp, CFG)
        except Exception:
            log(traceback.format_exc())


def pip_install(*pkgs):
    subprocess.run([sys.executable, "-m", "pip", "install", "-U", "--quiet", *pkgs],
                   check=True, timeout=300, creationflags=NOWIN)


def ensure_tools():
    """Garante ffmpeg, deno e segno (QR code) via pip, sem mexer no Windows."""
    try:
        import imageio_ffmpeg, deno  # noqa
    except ImportError:
        pip_install("imageio-ffmpeg", "deno")
        import imageio_ffmpeg, deno  # noqa
    try:
        import segno  # noqa
    except ImportError:
        try:
            pip_install("segno")
        except Exception:
            pass
    try:
        dn = deno.find_deno_bin()
    except FileNotFoundError:  # versão instalada: o Deno fica em runtime\\Scripts
        dn = os.path.join(_RT, "Scripts", "deno.exe")
    return imageio_ffmpeg.get_ffmpeg_exe(), dn


def update_ytdlp(force=False):
    """Atualiza o yt-dlp no máximo 1 vez a cada 24 h (o início do programa fica rápido e sem rede à toa)."""
    if getattr(sys, "frozen", False):
        return False
    stamp = os.path.join(HOME, "." + APP_SLUG + ".ytdlp")
    try:
        if not force and time.time() - os.path.getmtime(stamp) < 86400:
            return False
    except OSError:
        pass
    try:
        pip_install("yt-dlp[default]")
        with open(stamp, "w") as f:
            f.write(str(time.time()))
        for m in [m for m in sys.modules if m.startswith("yt_dlp")]:
            del sys.modules[m]
        UPDATED["done"] = True
        return True
    except Exception:
        return False


def common(deno_path=None):
    """Opções padrão do yt-dlp. Sem truques para driblar bloqueios; cookies.txt só se o usuário ativou em Ajustes."""
    o = {"quiet": True, "no_warnings": True}
    if deno_path:
        o["js_runtimes"] = {"deno": {"path": deno_path}}
    if CFGS.get("cookies_file"):
        cf = next((c for c in (os.path.join(HOME, "cookies.txt"),
                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt"))
                   if os.path.exists(c)), None)
        if cf:
            o["cookiefile"] = cf
    return o


def pace(gap=None):
    """Espaça os pedidos feitos ao site (evita sobrecarregá-lo)."""
    gap = CFGS.get("gap", 4.0) if gap is None else gap
    wait = PACE["t"] + gap + random.random() * 2 - time.time()
    if wait > 0:
        time.sleep(wait)
    PACE["t"] = time.time()


def video_id(url):
    m = re.search(r"(?:[?&]v=|youtu\.be/|shorts/|embed/|live/|/v/)([\w-]{11})", url or "")
    return m.group(1) if m else None


def ctype_for(path, audio=False):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".webm":
        return "audio/webm" if audio else "video/webm"
    if ext in DIRECT:
        return DIRECT[ext]
    return "audio/mp4" if audio else "video/mp4"


YT_RE = re.compile(r"^[\w-]{11}(\.f\d+)?\.(mp4|m4a|webm|mkv|opus|m4v)(\.part|\.ytdl)?$")
OUTTMPL = "%(title).90s [%(id)s].%(ext)s"  # nome do arquivo baixado: título + código (o código evita misturar vídeos)
NAMED_RE = re.compile(r"^.* \[[\w-]{11}\](\.f\d+)?\.(mp4|m4a|webm|mkv|opus|m4v)(\.part|\.ytdl)?$")  # "Título [código].mp4"
ID_IN_NAME = re.compile(r"(?:\[([\w-]{11})\]|^([\w-]{11}))(?:\.f\d+)?\.\w+$")
LOCAL_RE = re.compile(r"^local_[0-9a-f]{12}\.mp4(\.part\.mp4)?$")
VIS_RE = re.compile(r"^[0-9a-f]{16}\.mp4(\.part\.mp4|\.scene\.png)?$")  # telas Capa (pasta visuals)
JSON_RE = re.compile(r"^(?P<id>.+)\.(?:audio|video\d*)\.json$")


def unsafe_dir(d):
    """Pastas onde o programa nunca apaga nada: raiz do disco, pasta do usuário e pastas do Windows."""
    p = os.path.normcase(os.path.abspath(d))
    if os.path.dirname(p) == p or p == os.path.normcase(os.path.abspath(HOME)):
        return True
    for var in ("WINDIR", "ProgramFiles", "ProgramFiles(x86)", "ProgramData"):
        v = os.environ.get(var)
        if v and (p == os.path.normcase(os.path.abspath(v)) or p.startswith(os.path.normcase(os.path.abspath(v)) + os.sep)):
            return True
    return False


def cache_inventory():
    """Lista SÓ o que este programa criou na pasta de vídeos (nunca toca em outros arquivos).
    Devolve {"videos": [...], "temp": [...]}, cada item = (caminho, tamanho, data)."""
    inv = {"videos": [], "temp": []}
    d = CFGS["cache"]
    if not os.path.isdir(d) or unsafe_dir(d):
        return inv
    real = os.path.realpath(d)
    seen = set()

    def add(kind, name):
        p = os.path.join(d, name)
        if p in seen or os.path.islink(p) or not os.path.isfile(p) or os.path.dirname(os.path.realpath(p)) != real:
            return
        seen.add(p)
        st = os.stat(p)
        inv[kind].append((p, st.st_size, st.st_mtime))
    try:
        names = os.listdir(d)
    except OSError:
        return inv
    for n in names:
        m = JSON_RE.match(n)
        if not m:
            continue
        try:
            with open(os.path.join(d, n), encoding="utf-8") as f:
                data = json.load(f)
            media = os.path.basename(data["path"])
            if not (isinstance(data.get("ctype"), str) and media and not media.startswith(".")):
                continue  # não é um arquivo de controle deste programa: não mexe
        except Exception:
            continue
        if not data.get("local") and media in names:
            add("videos", media)
            add("videos", n)
        else:
            add("temp", n)  # arquivo de controle sem o vídeo: é só sobra
    vd = os.path.join(d, "visuals")
    if os.path.isdir(vd) and not os.path.islink(vd):
        rv = os.path.realpath(vd)
        try:
            vnames = os.listdir(vd)
        except OSError:
            vnames = []
        for n in vnames:
            m = VIS_RE.match(n)
            p = os.path.join(vd, n)
            if m and not os.path.islink(p) and os.path.isfile(p) and os.path.dirname(os.path.realpath(p)) == rv:
                st = os.stat(p)
                inv["temp" if m.group(1) else "videos"].append((p, st.st_size, st.st_mtime))
    for n in names:
        if n in ("",) or os.path.join(d, n) in seen:
            continue
        if LOCAL_RE.match(n) or ((YT_RE.match(n) or NAMED_RE.match(n))
                                 and (n.endswith((".part", ".ytdl")) or re.search(r"\.f\d+\.", n))):
            add("temp", n)
    return inv


BAD_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def safe_name(text, limit=100):
    """Nome de arquivo aceito pelo Windows, a partir de um título qualquer."""
    t = BAD_CHARS.sub(" ", str(text or "")).replace("\u200b", "")
    t = re.sub(r"\s+", " ", t).strip(" .")
    if len(t) > limit:
        t = t[:limit].rstrip(" .")
    if t.upper() in RESERVED:
        t += "_"
    return t


def file_id(name):
    """Código do YouTube escondido no nome do arquivo ('Título [abc...].mp4' ou 'abc....mp4'), ou None."""
    m = ID_IN_NAME.search(name or "")
    return (m.group(1) or m.group(2)) if m else None


def display_title(path):
    base = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r" \[[\w-]{11}\]$", "", base) or base


def downloaded_files():
    """Tudo o que já está baixado (pasta de vídeos + pasta da versão antiga), sem tocar nos arquivos:
    lista de dicts {title, path, size, mtime, audio, json, id}, do mais recente para o mais antigo."""
    out, seen = [], set()

    def add(p, title, jpath, audio_hint, vid):
        key = os.path.normcase(os.path.abspath(p))
        if key in seen or not os.path.isfile(p) or os.path.islink(p):
            return
        try:
            st = os.stat(p)
        except OSError:
            return
        if st.st_size < 1024:
            return
        seen.add(key)
        ext = os.path.splitext(p)[1].lower()
        out.append({"title": title or display_title(p), "path": p, "size": st.st_size, "mtime": st.st_mtime,
                    "audio": ext in AUDIO_EXT or audio_hint, "json": jpath, "id": vid or file_id(os.path.basename(p))})
    for d in _cache_dirs():
        if not os.path.isdir(d) or unsafe_dir(d):
            continue
        try:
            names = os.listdir(d)
        except OSError:
            continue
        for n in names:  # 1º os que têm arquivo de controle (trazem o título)
            m = JSON_RE.match(n)
            if not m:
                continue
            try:
                with open(os.path.join(d, n), encoding="utf-8") as f:
                    j = json.load(f)
                if j.get("local") or not isinstance(j.get("ctype"), str):
                    continue
                p = j["path"]
                title = (j.get("title") or "").strip() or None
            except Exception:
                continue
            add(p, title, os.path.join(d, n), ".audio." in n, m.group("id"))
        for n in names:  # 2º arquivos soltos
            low = n.lower()
            if (low.endswith(VIDEO_EXT + AUDIO_EXT) and not n.startswith("local_") and ".part" not in low
                    and ".norm." not in low and not re.search(r"\.f\d+\.", n)):
                add(os.path.join(d, n), None, None, False, None)
    out.sort(key=lambda x: -x["mtime"])
    return out


def rename_download(item, newname):
    """Troca o nome de um arquivo baixado (mantém o código do YouTube no fim, para o programa continuar
    reconhecendo o vídeo) e acerta o arquivo de controle. Devolve o novo caminho."""
    old = item["path"]
    d, ext = os.path.dirname(old), os.path.splitext(old)[1]
    base = safe_name(newname, 90)
    if not base:
        raise ValueError("empty")
    vid = item.get("id")
    stem = f"{base} [{vid}]" if vid else base
    new, n = os.path.join(d, stem + ext), 1
    same = os.path.normcase(new) == os.path.normcase(old)
    while not same and os.path.exists(new):
        n += 1
        new = os.path.join(d, f"{stem} ({n}){ext}")
    if not same:
        os.replace(old, new)
    jp = item.get("json")
    if jp and os.path.isfile(jp):
        try:
            with open(jp, encoding="utf-8") as f:
                j = json.load(f)
            j["path"], j["title"] = new, newname.strip()
            tmp = jp + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(j, f, ensure_ascii=False)
            os.replace(tmp, jp)
        except Exception:
            try:  # não conseguiu acertar o arquivo de controle: volta o nome para não perder o vídeo
                if not same:
                    os.replace(new, old)
            except OSError:
                pass
            raise
    return new


def delete_files(items, keep=()):
    """Apaga só o que veio do inventário. Devolve (apagados, bytes, mantidos_em_uso, erros)."""
    n = size = kept = 0
    errs = []
    keepn = {os.path.normcase(os.path.abspath(k)) for k in keep if k}
    for p, sz, _ in items:
        if os.path.normcase(os.path.abspath(p)) in keepn:
            kept += 1
            continue
        try:
            os.remove(p)
            n += 1
            size += sz
        except FileNotFoundError:
            pass
        except OSError as e:
            errs.append(str(e))
    return n, size, kept, errs


def fmt_size(b):
    for unit, div in (("GB", 1024 ** 3), ("MB", 1024 ** 2), ("KB", 1024)):
        if b >= div:
            v = f"{b / div:.1f}"
            return (v.replace(".", ",") if LANG["v"] == "pt" else v) + " " + unit
    return f"{int(b)} B"


def prune(keep=()):
    """Mantém a pasta de vídeos dentro do limite escolhido: apaga os vídeos MAIS ANTIGOS criados por este programa."""
    limit = float(CFGS["max_gb"]) * 1024 ** 3
    if limit <= 0:
        return
    try:
        inv = cache_inventory()
        delete_files([x for x in inv["temp"] if time.time() - x[2] > 86400])  # sobras com mais de 1 dia
        vids = sorted([x for x in inv["videos"] if not x[0].endswith(".json")], key=lambda x: x[2])
        total = sum(x[1] for x in vids)
        keepn = {os.path.normcase(os.path.abspath(k)) for k in keep if k}
        removed = False
        for p, sz, _ in vids:
            if total <= limit:
                break
            if os.path.normcase(os.path.abspath(p)) not in keepn:
                total -= sz
                delete_files([(p, sz, 0)])
                removed = True
        if removed:  # o arquivo de controle de um vídeo apagado não serve para mais nada
            delete_files([x for x in cache_inventory()["temp"] if JSON_RE.match(os.path.basename(x[0]))])
    except Exception:
        log(traceback.format_exc())


def trim_visuals(keep=None):
    """As telas da TV são temporárias: só a da faixa que está tocando (e a da próxima, feita durante a música) ficam no disco."""
    d = os.path.join(CFGS["cache"], "visuals")
    try:
        for n in os.listdir(d):
            p = os.path.join(d, n)
            if re.fullmatch(r"[0-9a-f]{16}\.mp4", n) and not (keep and os.path.normcase(p) == os.path.normcase(keep)):
                os.remove(p)
    except OSError:
        pass


def fmt_for(mode):
    """Formato do yt-dlp conforme o modo/qualidade ('audio', 'video' = automática, 'video720'...)."""
    if mode == "audio":
        return "ba[ext=m4a]/ba/b"
    q = int(mode[5:]) if len(mode) > 5 else 1080
    if q > 1080:
        return (f"bv*[height<={q}][vcodec^=vp09]+ba[ext=m4a]/bv*[height<={q}][vcodec^=avc1]+ba[ext=m4a]/"
                f"bv*[height<={q}]+ba/b[height<={q}]/b")
    return (f"bv*[vcodec^=avc1][height<={q}]+ba[ext=m4a]/bv*[vcodec^=avc1][height<={q}]+ba/"
            f"b[ext=mp4][height<={q}]/b[height<={q}]/b")


def mkey():
    if CFGS["mode"] == "audio":
        return "audio"
    q = str(CFGS.get("quality", "auto"))
    return "video" if q == "auto" else f"video{q}"


VIDEO_EXT = (".mp4", ".m4v", ".webm", ".mkv")
AUDIO_EXT = (".m4a", ".opus", ".aac", ".mp3")
LEGACY_DIRS = ("ChromecastPlayerCache",)  # pasta da versão antiga do programa: os vídeos de lá também valem


def _cache_dirs():
    main = os.path.normcase(os.path.abspath(CFGS["cache"]))
    ds = [CFGS["cache"]]
    for n in LEGACY_DIRS:
        d = os.path.join(HOME, n)
        if os.path.isdir(d) and os.path.normcase(os.path.abspath(d)) != main:
            ds.append(d)
    return ds


def _load_json(d, name):
    try:
        with open(os.path.join(d, name), encoding="utf-8") as f:
            j = json.load(f)
        if isinstance(j, dict) and os.path.isfile(j["path"]):
            os.utime(j["path"])
            return j
    except Exception:
        pass
    return None


_LS = {}


def _names(d):
    """Lista da pasta, relida só quando a pasta muda (procurar vídeo por vídeo numa fila grande fica rápido)."""
    st = os.stat(d)
    k = os.path.normcase(os.path.abspath(d))
    hit = _LS.get(k)
    if hit and hit[0] == st.st_mtime_ns and time.time() - hit[2] < 30:
        return hit[1]
    names = sorted(os.listdir(d))
    _LS[k] = (st.st_mtime_ns, names, time.time())
    return names


def _cached(vid, mode):
    """Acha um item JÁ BAIXADO, sem pedir nada ao site: mesmo modo, outra qualidade de vídeo, arquivo solto
    (sem o .json) ou a pasta da versão antiga. Para vídeo aceita qualquer qualidade que já esteja na pasta."""
    if not vid:
        return None
    audio = mode == "audio"
    for d in _cache_dirs():
        try:
            names = _names(d)
        except OSError:
            continue
        order = [f"{vid}.{mode}.json"] + [n for n in names if not audio and n != f"{vid}.{mode}.json"
                                          and n.startswith(vid + ".video") and n.endswith(".json")]
        for n in order:
            j = _load_json(d, n)
            if j:
                return j
        exts = AUDIO_EXT if audio else VIDEO_EXT
        found = []
        for n in names:
            m = re.fullmatch(r"(?:.* \[" + re.escape(vid) + r"\]|" + re.escape(vid) + r")\.(\w+)", n)
            p = os.path.join(d, n)
            if m and ("." + m.group(1).lower()) in exts and os.path.isfile(p) and os.path.getsize(p) > 1024:
                found.append((exts.index("." + m.group(1).lower()), p))
        if found:
            p = sorted(found)[0][1]
            info = {"path": p, "title": display_title(p),
                    "duration": None, "height": None, "ctype": ctype_for(p, audio),
                    "thumb": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg", "artist": ""}
            if os.path.normcase(os.path.abspath(d)) == os.path.normcase(os.path.abspath(CFGS["cache"])):
                try:  # registra, para a contagem e a limpeza da pasta enxergarem este vídeo
                    with open(os.path.join(d, f"{vid}.{mode}.json"), "w", encoding="utf-8") as f:
                        json.dump(info, f, ensure_ascii=False)
                except OSError:
                    pass
            os.utime(p)
            return info
    return None


def _download(url, ffmpeg, deno_path, mode, progress=None):
    import yt_dlp
    os.makedirs(CFGS["cache"], exist_ok=True)
    audio = mode == "audio"
    fmt = fmt_for(mode)

    def hook(d):
        if progress and d.get("status") == "downloading":
            tot = d.get("total_bytes") or d.get("total_bytes_estimate")
            if tot:
                progress(int(d.get("downloaded_bytes", 0) * 100 / tot))
    opts = common(deno_path)
    opts.update(noplaylist=True, format=fmt, ffmpeg_location=ffmpeg,
                outtmpl=os.path.join(CFGS["cache"], OUTTMPL), windowsfilenames=True,
                progress_hooks=[hook], noprogress=True)
    if not audio:
        opts["merge_output_format"] = "mp4"
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
    path = (info.get("requested_downloads") or [{}])[0].get("filepath")
    if not path:
        c = [f for f in os.listdir(CFGS["cache"]) if (f.startswith(info["id"] + ".") or f"[{info['id']}]" in f)
             and not f.endswith((".json", ".part"))]
        path = os.path.join(CFGS["cache"], c[0])
    if CFGS.get("norm"):  # volume uniforme: só mexe no som, o vídeo é copiado
        mediatools.normalize(ffmpeg, path)
    d = {"path": path, "title": info.get("title") or T("untitled"), "duration": info.get("duration"),
         "height": info.get("height"), "ctype": ctype_for(path, audio),
         "thumb": info.get("thumbnail"), "artist": info.get("artist") or info.get("uploader") or ""}
    with open(os.path.join(CFGS["cache"], f"{info['id']}.{mode}.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    return d


def fetch_video(url, vid, ffmpeg, deno_path, mode, progress=None, on_update=None):
    """Devolve a mídia já baixada. Se ela já está na pasta, não pede nada ao site."""
    vid = vid or video_id(url)
    c = _cached(vid, mode) if vid else None
    if c:
        return c
    pace()
    try:
        return _download(url, ffmpeg, deno_path, mode, progress)
    except Exception as e:
        if UPDATED["done"] or BOT in str(e):
            raise
        UPDATED["done"] = True
        if on_update:
            on_update()
        if update_ytdlp():
            return _download(url, ffmpeg, deno_path, mode, progress)
        raise


_CODEC = {}


def codec_of(ffmpeg, path):
    """Codec do vídeo, lido uma vez por arquivo (ler de novo a cada tela travaria o programa com muitos arquivos)."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    k = (path, st.st_mtime, st.st_size)
    if k not in _CODEC:
        if len(_CODEC) > 2000:
            _CODEC.clear()
        _CODEC[k] = mediatools.video_codec(ffmpeg, path) if ffmpeg else None
    return _CODEC[k]


def prepare_local(path, ffmpeg, convert=True):
    """Arquivo do PC: toca direto se o Chromecast aceita; senão converte (copia o que der)."""
    ext = os.path.splitext(path)[1].lower()
    title = display_title(path)  # sem o "[código]" que os arquivos baixados levam no nome
    hevc_ok = bool(CFGS.get("hevc"))
    if ext in DIRECT:
        # vídeo de câmera/celular costuma vir em H.265: só toca direto se a TV aceitar
        if ext not in (".mp4", ".m4v") or hevc_ok or codec_of(ffmpeg, path) != "hevc":
            return {"path": path, "title": title, "ctype": DIRECT[ext], "local": True}
    norm = bool(CFGS.get("norm"))
    key = hashlib.sha1(f"{path}|{os.path.getmtime(path)}|{os.path.getsize(path)}|{int(hevc_ok)}|{int(norm)}".encode(),
                       usedforsecurity=False).hexdigest()[:12]
    out = os.path.join(CFGS["cache"], f"local_{key}.mp4")
    if not os.path.isfile(out):
        if not convert:
            return None
        os.makedirs(CFGS["cache"], exist_ok=True)
        probe = subprocess.run([ffmpeg, "-hide_banner", "-i", path], capture_output=True,
                               text=True, creationflags=NOWIN).stderr
        v = re.search(r"Video: (\w+)", probe)
        a = re.search(r"Audio: (\w+)", probe)
        cmd = [ffmpeg, "-loglevel", "error", "-y", "-i", path, "-map", "0:v:0?", "-map", "0:a:0?"]
        if v:
            if v.group(1) == "h264":
                cmd += ["-c:v", "copy"]
            elif v.group(1) == "hevc" and hevc_ok:
                cmd += ["-c:v", "copy", "-tag:v", "hvc1"]
            else:
                cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p"]
        if a:
            if norm:
                cmd += ["-af", mediatools.LOUDNORM, "-c:a", "aac", "-b:a", "192k"]
            else:
                cmd += ["-c:a", "copy"] if a.group(1) in ("aac", "mp3") else ["-c:a", "aac", "-b:a", "192k"]
        tmp = out + ".part.mp4"
        r = subprocess.run(cmd + ["-movflags", "+faststart", tmp], capture_output=True,
                           text=True, creationflags=NOWIN)
        if r.returncode != 0:
            raise RuntimeError(T("err_convert", e=r.stderr[-200:]))
        os.replace(tmp, out)
    return {"path": out, "title": title, "ctype": "video/mp4", "local": True}


def load_tracks(url, deno_path=None):
    """Devolve (lista de faixas, posição inicial). Link sem 'list=' vira 1 faixa."""
    if "list=" not in url:
        return [{"id": video_id(url), "title": url, "url": url}], 0
    import yt_dlp
    opts = common(deno_path)
    opts.update(extract_flat="in_playlist", playlistend=100)
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=False)
    tracks = []
    for e in (info.get("entries") or []):
        if not e:
            continue
        u = e.get("url") or ""
        if not u.startswith("http"):
            u = f"https://www.youtube.com/watch?v={e.get('id')}"
        tracks.append({"id": e.get("id"), "title": e.get("title") or e.get("id"), "url": u})
    if not tracks:
        return [{"id": video_id(url), "title": info.get("title", url), "url": url}], 0
    m = re.search(r"[?&]v=([\w-]{11})", url)
    start = 0
    if m:
        for i, t in enumerate(tracks):
            if t["id"] == m.group(1):
                start = i
                break
    return tracks, start


def tkey(t):
    return t.get("url") or t.get("path")


def lan_ip(host="8.8.8.8"):
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((host, 8009))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class Watcher:
    """Avisa o app quando a música termina."""

    def __init__(self, app):
        self.app = app

    def new_media_status(self, status):
        try:
            if status.player_state == "IDLE" and status.idle_reason == "FINISHED":
                self.app.on_finished()
        except Exception:
            log(traceback.format_exc())


def is_lan_ip(ip):
    """Só aceita quem está na rede local (privada), no próprio computador ou em link-local. Nunca a internet."""
    import ipaddress
    try:
        a = ipaddress.ip_address(ip.split("%")[0])
        if getattr(a, "ipv4_mapped", None):
            a = a.ipv4_mapped
        return a.is_private or a.is_loopback or a.is_link_local
    except ValueError:
        return False


class Guard:
    """Bloqueia por 1 minuto quem errar a senha 8 vezes seguidas."""

    def __init__(self, limit=8, window=60):
        self.limit, self.window, self.fails = limit, window, {}
        self.lock = threading.Lock()

    def blocked(self, ip):
        with self.lock:
            now = time.time()
            self.fails[ip] = [t for t in self.fails.get(ip, []) if now - t < self.window]
            return len(self.fails[ip]) >= self.limit

    def fail(self, ip):
        with self.lock:
            self.fails.setdefault(ip, []).append(time.time())
            if len(self.fails) > 500:
                self.fails = {k: v for k, v in self.fails.items() if v and time.time() - v[-1] < self.window}


def valid_media_url(u):
    """Só links http(s) comuns; nunca file:, caminhos locais ou esquemas estranhos."""
    if not isinstance(u, str) or not u or len(u) > 2048 or any(ch in u for ch in "\r\n\x00 "):
        return False
    try:
        p = urllib.parse.urlparse(u)
    except ValueError:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc) and "@" not in p.netloc


SEC = {"X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY",
       "Cache-Control": "no-store"}
CSP_REMOTE = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; "
              "img-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
CSP_PC = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; "
          "media-src http://127.0.0.1:*; img-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


def serve_in_thread(handler, port=0):
    import http.server, socket, socketserver

    class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        # No Windows, "reusar endereço" deixaria outro programa ocupar a mesma porta; lá a porta fica exclusiva.
        allow_reuse_address = not sys.platform.startswith("win")
        request_queue_size = 32

        def server_bind(self):
            if sys.platform.startswith("win") and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                try:
                    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                except OSError:
                    pass
            super().server_bind()

        def handle_error(self, request, client_address):
            # A TV e o celular fecham conexões no meio o tempo todo (pular, pausar, trocar de app): isso é normal.
            e = sys.exc_info()[1]
            if not isinstance(e, (ConnectionError, TimeoutError, socket.timeout)):
                log("servidor local: " + traceback.format_exc())
    try:
        srv = S(("0.0.0.0", port), handler)
    except OSError:
        srv = S(("0.0.0.0", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


class FileServer:
    """Entrega os arquivos ao Chromecast (com suporte a pular para qualquer ponto)."""

    def __init__(self):
        import http.server
        self.reg, self.by_path = {}, {}
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            timeout = 120  # conexão parada (a TV pausou ou caiu) é encerrada; a TV reabre sozinha quando precisar

            def log_message(self, *a):
                pass

            def _send(self, body):
                if not is_lan_ip(self.client_address[0]):
                    self.send_error(403)
                    return
                parts = urllib.parse.unquote(self.path.split("?")[0]).split("/")
                p = outer.reg.get(parts[2]) if len(parts) > 3 else None
                if not p or not os.path.isfile(p):
                    self.send_error(404)
                    return
                size = os.path.getsize(p)
                start, end, code = 0, size - 1, 200
                m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range") or "")
                if m:
                    a, b = m.groups()
                    if a == "" and b != "":
                        start = max(0, size - int(b))
                    else:
                        start = int(a or 0)
                        end = min(int(b), size - 1) if b else size - 1
                    if start > end:
                        self.send_response(416)
                        self.send_header("Content-Range", f"bytes */{size}")
                        self.end_headers()
                        return
                    code = 206
                self.send_response(code)
                ext = os.path.splitext(p)[1].lower()
                self.send_header("Content-Type", "text/vtt; charset=utf-8" if ext == ".vtt"
                                 else DIRECT.get(ext, "video/mp4"))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", str(end - start + 1))
                if code == 206:
                    self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                if not body:
                    return
                try:
                    with open(p, "rb") as f:
                        f.seek(start)
                        left = end - start + 1
                        while left > 0:
                            chunk = f.read(min(262144, left))
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            left -= len(chunk)
                except OSError:
                    pass

            def do_GET(self):
                self._send(True)

            def do_HEAD(self):
                self._send(False)
        self.srv = serve_in_thread(H)
        self.port = self.srv.server_address[1]

    def url_for(self, path, cast_host):
        tok = self.by_path.get(path)
        if not tok:
            tok = self.by_path[path] = secrets.token_urlsafe(12)
        self.reg[tok] = path
        return f"http://{lan_ip(cast_host)}:{self.port}/f/{tok}/{urllib.parse.quote(os.path.basename(path))}"


def page_text(text):
    """Texto traduzido que vai dentro da página do celular/PC (HTML e JavaScript): sem caracteres que quebrem a página."""
    return (str(text).replace("\\", "/").replace("'", "’").replace('"', "”").replace("<", "‹").replace(">", "›")
            .replace("&", "e").replace("\n", " "))


def remote_html():
    h = REMOTE_HTML
    for k in set(re.findall(r"@@(\w+)@@", h)):
        h = h.replace("@@" + k + "@@", page_text(T(k)))
    return h


class RemoteServer:
    """Página de controle para abrir no celular (mesma rede Wi-Fi)."""

    def __init__(self, app, port=8765):
        import http.server
        outer = self
        self.app = app
        self.guard = Guard()

        class H(http.server.BaseHTTPRequestHandler):
            timeout = 20  # celular que abre a conexão e não manda nada não prende o programa

            def log_message(self, *a):
                pass

            def _ok(self):
                ip = self.client_address[0]
                if not is_lan_ip(ip):
                    self.send_error(403)
                    return False
                if outer.guard.blocked(ip):
                    self.send_error(429)
                    return False
                q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                if not hmac.compare_digest(q.get("k", [""])[0].encode("utf-8"), outer.app.token.encode("utf-8")):
                    outer.guard.fail(ip)
                    self.send_error(403)
                    return False
                return True

            def _hdr(self, csp=None):
                for k, v in SEC.items():
                    self.send_header(k, v)
                if csp:
                    self.send_header("Content-Security-Policy", csp)

            def _json(self, obj):
                data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self._hdr()
                self.end_headers()
                self.wfile.write(data)

            def _local(self):
                if self.client_address[0] not in ("127.0.0.1", "::1"):
                    self.send_error(403)
                    return False
                return True

            def do_GET(self):
                if not self._ok():
                    return
                path = urllib.parse.urlparse(self.path).path
                if path == "/pc":
                    if not self._local():
                        return
                    data = pc_html().encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self._hdr(CSP_PC)
                    self.end_headers()
                    self.wfile.write(data)
                    return
                if path == "/api/state":
                    self._json(outer.app.remote_state())
                else:
                    data = remote_html().encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self._hdr(CSP_REMOTE)
                    self.end_headers()
                    self.wfile.write(data)

            def do_POST(self):
                if not self._ok():
                    return
                if urllib.parse.urlparse(self.path).path == "/pc/sync":
                    if not self._local():
                        return
                    try:
                        n = max(0, min(int(self.headers.get("Content-Length") or 0), 65536))
                        rep = json.loads(self.rfile.read(n) or b"{}")
                        self._json({"cmds": outer.app.get_pcdev().sync(rep)})
                    except Exception:
                        log(traceback.format_exc())
                        self._json({"cmds": []})
                    return
                try:
                    n = max(0, min(int(self.headers.get("Content-Length") or 0), 65536))
                    body = json.loads(self.rfile.read(n) or b"{}")
                    if isinstance(body, dict):
                        outer.app.remote_cmd(body.get("name"), body.get("arg"))
                except Exception:
                    log(traceback.format_exc())
                self._json(outer.app.remote_state())
        self.srv = serve_in_thread(H, port)
        self.port = self.srv.server_address[1]


PALETTES = {
    "Claro": dict(bg="#f4f6fb", surface="#ffffff", surface2="#eef1f7", border="#d9dfeb", text="#172033",
                  muted="#667089", accent="#2f6bff", accent2="#1f55df", accent_soft="#e3ecff", on_accent="#ffffff",
                  ok="#12a066", warn="#c27a00", bad="#d33a3a"),
    "Escuro": dict(bg="#0f1115", surface="#171a21", surface2="#222733", border="#2c3240", text="#e9ecf3",
                   muted="#8f98ad", accent="#5b8cff", accent2="#84a8ff", accent_soft="#26335a", on_accent="#ffffff",
                   ok="#3ddc97", warn="#ffb454", bad="#ff6b6b"),
}
FAMILY = "Segoe UI"
FONT_NAME = "DejaVu Sans Mono"  # fonte embutida em assets/fonts (licença livre); se faltar, usa a Segoe UI


def pick_family():
    """Carrega a fonte embutida só para este programa (não instala nada no Windows) e devolve o nome a usar."""
    try:
        import tkinter.font as tkfont
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
        if sys.platform.startswith("win"):
            import ctypes
            for n in ("DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf"):
                f = os.path.join(d, n)
                if os.path.isfile(f):
                    ctypes.windll.gdi32.AddFontResourceExW(f, 0x10, 0)  # FR_PRIVATE: vale só para este processo
        if FONT_NAME in tkfont.families():
            return FONT_NAME
    except Exception:
        pass
    return FAMILY
SIZES = {"Compacto": (0.85, 9), "Normal": (1.0, 10), "Grande": (1.15, 11)}
COLORMAP = {"orange": "warn", "green": "ok", "red": "bad"}


def enable_dpi():
    """Avisa o Windows que o programa sabe lidar com telas ampliadas (125%, 150%...): fim do desfoque."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class Slider(tk.Canvas):
    """Barra deslizante moderna (linha do tempo e volume)."""

    def __init__(self, parent, pal, k, command=None, press=None, release=None, maximum=100.0, height=26,
                 width=60):
        super().__init__(parent, width=int(width * k), height=int(height * k), bg=pal["surface"],
                         highlightthickness=0, bd=0, cursor="hand2")
        self.pal, self.k = pal, k
        self.cmd, self.pcb, self.rcb = command, press, release
        self.max, self.val, self.drag, self.hover = float(maximum), 0.0, False, False
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<ButtonPress-1>", self._down)
        self.bind("<B1-Motion>", self._move)
        self.bind("<ButtonRelease-1>", self._up)
        self.bind("<Enter>", lambda e: self._hv(True))
        self.bind("<Leave>", lambda e: self._hv(False))

    def _hv(self, v):
        self.hover = v
        self.draw()

    def config(self, **kw):
        if "to" in kw:
            self.max = max(1.0, float(kw.pop("to")))
            self.draw()
        if kw:
            super().config(**kw)
    configure = config

    def get(self):
        return self.val

    def set(self, v):
        if not self.drag:
            self.val = min(max(0.0, float(v)), self.max)
            self.draw()

    def _at(self, x):
        pad = int(9 * self.k)
        w = max(1, self.winfo_width() - 2 * pad)
        return min(max(0.0, (x - pad) / w), 1.0) * self.max

    def _down(self, e):
        self.drag = True
        if self.pcb:
            self.pcb()
        self._move(e)

    def _move(self, e):
        if self.drag:
            self.val = self._at(e.x)
            self.draw()
            if self.cmd:
                self.cmd(self.val)

    def _up(self, e):
        if self.drag:
            self.drag = False
            self.val = self._at(e.x)
            self.draw()
            if self.rcb:
                self.rcb(self.val)

    def draw(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20:
            return
        k, p = self.k, self.pal
        pad, y, th = int(9 * k), h // 2, max(4, int(5 * k))
        xv = pad + (w - 2 * pad) * (self.val / self.max)
        self.delete("all")
        t2 = th / 2
        rrect(self, pad - t2, y - t2, w - pad + t2, y + t2, t2, fill=p["border"], outline="")
        if xv > pad:
            rrect(self, pad - t2, y - t2, xv + t2, y + t2, t2, fill=p["accent"], outline="")
        r = int((8 if (self.hover or self.drag) else 6) * k)
        oval(self, xv - r, y - r, xv + r, y + r, fill=p["accent2"] if self.drag else p["accent"],
             outline=p["surface"], width=max(1, int(2 * k)))


class Flow(tk.Frame):
    """Linha que 'quebra' sozinha: se faltar largura, os itens descem para a linha de baixo (nada some)."""
    hook = None

    def __init__(self, parent, bg, gap=8, vgap=6, align="left", valign="center"):
        super().__init__(parent, bg=bg, height=1, width=1, highlightthickness=0, bd=0)
        self.items, self.gap, self.vgap, self.align, self.valign = [], gap, vgap, align, valign
        self.hidden = set()
        self.w, self.sig, self.job, self.h = 0, None, None, 0
        self.bind("<Configure>", self._conf)

    def add(self, widget, grow=False):
        self.items.append((widget, grow))
        widget.bind("<Configure>", lambda e: self._sched(), add="+")
        self._sched()

    def show(self, widget, flag=True):
        """Mostra ou esconde um item da linha (os outros se reorganizam)."""
        if flag == (widget not in self.hidden):
            return
        (self.hidden.discard if flag else self.hidden.add)(widget)
        if not flag:
            widget.place_forget()
        self.sig = None
        self._sched()

    def _conf(self, e):
        if e.width != self.w:
            self.w = e.width
            self._sched()

    def _sched(self):
        if self.job is None:
            self.job = self.after_idle(self.layout)

    def layout(self):
        self.job = None
        try:
            W = self.winfo_width()
            if W <= 1 or not self.items:
                return
            sizes = [(w, g, w.winfo_reqwidth(), w.winfo_reqheight()) for w, g in self.items if w not in self.hidden]
            if not sizes:
                self.config(height=1)
                return
            sig = (W, tuple((s[2], s[3]) for s in sizes))
            if sig == self.sig:
                return
            self.sig = sig
            lines, cur, curw = [], [], 0
            for it in sizes:
                need = it[2] + (self.gap if cur else 0)
                if cur and curw + need > W:
                    lines.append(cur)
                    cur, curw, need = [], 0, it[2]
                cur.append(it)
                curw += need
            if cur:
                lines.append(cur)
            y = 0
            for ln in lines:
                used = sum(i[2] for i in ln) + self.gap * (len(ln) - 1)
                extra = max(0, W - used)
                gr = [i for i in ln if i[1]]
                share = extra // len(gr) if gr else 0
                lh = max(i[3] for i in ln)
                x = 0 if gr else {"left": 0, "center": extra // 2, "right": extra}[self.align]
                for w, g, rw, rh in ln:
                    ww = rw + (share if g else 0)
                    w.place(x=x, y=y + ((lh - rh) // 2 if self.valign == "center" else 0), width=ww, height=rh)
                    x += ww + self.gap
                y += lh + self.vgap
            H = max(1, y - self.vgap)
            self.config(height=H, width=max(i[2] for i in sizes))
            if H != self.h:
                self.h = H
                if Flow.hook:
                    Flow.hook()
        except tk.TclError:
            pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # a janela só aparece pronta: nada de ver a tela sendo montada aos poucos
        dpi = float(os.environ.get("CP_DPI") or self.winfo_fpixels("1i"))
        self.k = max(1.0, dpi / 96.0)
        self.tk.call("tk", "scaling", dpi / 72.0)
        self.cfg = load_cfg()
        set_lang(self.cfg.get("lang") or detect_lang())
        self.title(T("app_title"))
        try:
            ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if sys.platform.startswith("win") and os.path.isfile(ico):
                self.iconbitmap(default=ico)
        except Exception:
            pass
        try:  # vários tamanhos do MESMO ícone: o Windows escolhe o que casa com a escala da tela (barra de título nítida)
            pngs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "png")
            self._icons = [tk.PhotoImage(master=self, file=os.path.join(pngs, f"icon_{n}.png"))
                           for n in (16, 20, 24, 32, 40, 48, 64, 128, 256)]
            self.iconphoto(True, *self._icons)
        except Exception:
            pass
        self.size_name = self.cfg.get("size") if self.cfg.get("size") in SIZES else "Compacto"
        self.uf, self.fs = SIZES[self.size_name]
        self.u = self.k * self.uf
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(int(900 * self.uf * self.k), int(sw * 0.92)), min(int(700 * self.uf * self.k), int(sh * 0.88))
        self.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 3)}")
        self._fit_job = None
        CFGS.update(cookies_file=bool(self.cfg.get("cookies_file", False)), mode=self.cfg.get("mode", "video"),
                 screen="cover",
                 subs=self.cfg.get("subs") if self.cfg.get("subs") in ("off", "pt", "en") else "off",
                 norm=bool(self.cfg.get("norm", False)), hevc=bool(self.cfg.get("hevc", False)),
                    max_gb=float(self.cfg.get("max_gb", 3)))
        if self.cfg.get("cache"):
            CFGS["cache"] = self.cfg["cache"]
        self.theme = self.cfg.get("theme") if self.cfg.get("theme") in PALETTES else "Claro"
        self.pal = PALETTES[self.theme]
        old = self.cfg.get("token")
        self.token = old if (isinstance(old, str) and len(old) >= 20) else secrets.token_urlsafe(18)
        self.cfg["token"] = self.token
        CFGS["quality"] = str(self.cfg.get("quality", "auto"))
        self.cast = self.browser = self.tools = self.server = self.remote = None
        self.chromecast = self.pcdev = None
        self.switching = False
        self.devices = {}
        self.tracks, self.orig, self.idx = [], None, 0
        self.cache, self.failed = {}, set()
        self.cur_path = ""
        self.armed = self.playing = False
        self.repeat_on = self.shuffle_on = self.stop_after = self.bulk = False
        self.sleep_at, self.blocked_until, self.block_msg_until = None, 0.0, 0.0
        self.latency, self.adjust = 2.0, float(self.cfg.get("adjust", 0))
        self.lookahead = int(self.cfg.get("lookahead", 3))
        self.pos = self.dur_now = self.dur = 0
        self.cur_title, self.last_msg = "", ""
        self.dragging = self.updating = self.vol_drag = False
        self._vol_t, self._shown_playing = 0.0, None
        self.play_lock, self.fetch_lock, self.cfg_lock = (threading.Lock(), threading.Lock(),
                                                          threading.Lock())
        self.closing = False
        self.vis_lock, self.vis_failed = threading.Lock(), set()
        self.space_level, self.space_nums = 0, None
        self._dl_lock, self._dl_busy, self._dl_again = threading.Lock(), False, False
        self.q = queue.Queue()
        self.status_state, self.now_state = ("st_starting", {}, "orange"), None
        self.log_lines, self.msg_view, self.queue_name, self.vol_val, self.cur_dev = [], None, "", 50, ""
        self.sel_pl = None
        self.target = self.cfg.get("target") if self.cfg.get("target") in ("cast", "pc") else "cast"
        self.off_since, self.retry_n, self.next_retry, self.reconnecting, self.gave_up = None, 0, 0, False, False
        self.v_shuf, self.v_rep = tk.BooleanVar(), tk.BooleanVar()
        self.folds, self.page_folds, self.last_open, self.cur_page, self._cur = {}, {}, None, "play", "play"
        self.auto_closed, self._fit_lock, self._reopen_sig = [], False, None
        self.frame = winframe.install(self)  # barra de título própria (None = barra padrão do Windows)
        self._style()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._keys()
        self.after(100, self.drain)
        for ms in (50, 600, 2500):  # repete: o Windows às vezes recoloca o ícone quando a janela termina de abrir
            if not self.frame:
                self.after(ms, lambda: hide_title_icon(self))
        self.bg(self.prepare)
        self.discover()
        for fn in (self.poll, self.downloader):
            threading.Thread(target=fn, daemon=True).start()
        self.after_idle(self._reveal)

    def _show_now(self):
        try:
            self.fit_window()
            self.update_idletasks()
        except Exception:
            log(traceback.format_exc())
        try:
            self.attributes("-alpha", 1.0)
        except tk.TclError:
            pass

    def _reveal(self):
        """Mostra a janela já montada, medida e encaixada, de uma vez só."""
        try:
            for _ in range(3):  # medir, ajustar e medir de novo até o tamanho assentar
                before = (self.winfo_width(), self.winfo_height(), self.winfo_reqwidth(), self.winfo_reqheight())
                self.fit_window()
                self.update_idletasks()
                if before == (self.winfo_width(), self.winfo_height(), self.winfo_reqwidth(), self.winfo_reqheight()):
                    break
            if getattr(self, "frame", None):
                self.frame.taskbar_button(hidden=True)
        except Exception:
            log(traceback.format_exc())
        finally:
            try:  # entra transparente, deixa o desenho assentar e só então fica visível (sem "montar na frente do olho")
                self.attributes("-alpha", 0.0)
                fade = True
            except tk.TclError:
                fade = False
            self.deiconify()
            self.lift()
            try:
                self.focus_force()
            except Exception:
                pass
            if fade:
                self.after(220, self._show_now)
        self.bg(lambda: (trim_visuals(), self.refresh_usage()))
        if self.cfg.get("terms_ok") != TERMS_VERSION:
            self.after(300, self.ask_terms)

    # ---------- aparência ----------
    def px(self, v):
        return int(v * self.u)

    def _style(self):
        import tkinter.font as tkfont
        global FAMILY
        FAMILY = pick_family()
        p, px = self.pal, self.px
        efs = self.fs - (1 if FAMILY == FONT_NAME else 0)  # a fonte embutida é mais larga: 1 pt a menos compensa
        UI.update(pal=p, u=self.u, fam=FAMILY, fs=efs)
        self.configure(bg=p["bg"])
        for n in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            tkfont.nametofont(n).configure(family=FAMILY, size=efs)
        mk = lambda **kw: tkfont.Font(family=FAMILY, **kw)
        fs = efs
        self.f_title, self.f_big = mk(size=fs + 7, weight="bold"), mk(size=fs + 3, weight="bold")
        self.f_head, self.f_small = mk(size=fs, weight="bold"), mk(size=fs)
        self.f_icon, self.f_play = mk(size=fs + 4), mk(size=fs + 8)
        self.f_mono = tkfont.Font(family=FAMILY, size=9)
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=p["bg"], foreground=p["text"], fieldbackground=p["surface2"],
                    bordercolor=p["border"], lightcolor=p["border"], darkcolor=p["border"],
                    troughcolor=p["surface2"], focuscolor=p["surface"])
        s.configure("TFrame", background=p["bg"])
        s.configure("Card.TFrame", background=p["surface"])
        s.configure("TLabel", background=p["bg"], foreground=p["text"])
        s.configure("Muted.TLabel", background=p["bg"], foreground=p["muted"])
        s.configure("Card.TLabel", background=p["surface"], foreground=p["text"])
        s.configure("CardMuted.TLabel", background=p["surface"], foreground=p["muted"])
        s.configure("CardTitle.TLabel", background=p["surface"], foreground=p["muted"], font=self.f_head)
        s.configure("Big.TLabel", background=p["surface"], foreground=p["text"], font=self.f_big)
        pad = (px(12), px(6))
        s.configure("TButton", background=p["surface2"], foreground=p["text"], borderwidth=0, relief="flat",
                    padding=pad, focusthickness=0, font=self.f_small)
        s.map("TButton", background=[("active", p["border"]), ("disabled", p["surface"])],
              foreground=[("disabled", p["muted"])])
        s.configure("Accent.TButton", background=p["accent"], foreground=p["on_accent"], padding=(px(18), px(9)),
                    font=self.f_head)
        s.map("Accent.TButton", background=[("active", p["accent2"])])
        s.configure("Icon.TButton", font=self.f_icon, padding=(px(12), px(6)))
        s.configure("Play.TButton", background=p["accent"], foreground=p["on_accent"], font=self.f_play,
                    padding=(px(18), px(6)))
        s.map("Play.TButton", background=[("active", p["accent2"])])
        s.configure("Skip.TButton", font=self.f_small, padding=(px(8), px(6)))
        s.configure("Toggle.TButton", font=self.f_icon, padding=(px(12), px(6)), foreground=p["muted"])
        s.configure("ToggleOn.TButton", font=self.f_icon, padding=(px(12), px(6)), background=p["accent"],
                    foreground=p["on_accent"])
        s.map("ToggleOn.TButton", background=[("active", p["accent2"])])
        s.configure("TEntry", fieldbackground=p["surface2"], foreground=p["text"], insertcolor=p["text"],
                    padding=(px(8), px(7)), borderwidth=1)
        s.configure("TCombobox", fieldbackground=p["surface2"], background=p["surface2"], foreground=p["text"],
                    arrowcolor=p["muted"], padding=(px(6), px(5)), selectbackground=p["surface2"],
                    selectforeground=p["text"])
        s.map("TCombobox", fieldbackground=[("readonly", p["surface2"])], foreground=[("readonly", p["text"])])
        s.configure("TSpinbox", fieldbackground=p["surface2"], background=p["surface2"], foreground=p["text"],
                    arrowcolor=p["muted"], insertcolor=p["text"], padding=(px(6), px(5)))
        for n in ("TCheckbutton", "TRadiobutton"):
            s.configure(n, background=p["surface"], foreground=p["text"], indicatorcolor=p["surface2"],
                        focusthickness=0)
            s.map(n, indicatorcolor=[("selected", p["accent"])], background=[("active", p["surface"])])
        s.configure("Vertical.TScrollbar", background=p["border"], troughcolor=p["surface2"], arrowcolor=p["muted"],
                    bordercolor=p["surface2"], relief="flat", gripcount=0)
        s.map("Vertical.TScrollbar", background=[("active", p["muted"])])
        self.option_add("*TCombobox*Listbox.background", p["surface2"])
        self.option_add("*TCombobox*Listbox.foreground", p["text"])
        self.option_add("*TCombobox*Listbox.selectBackground", p["accent"])
        self.option_add("*TCombobox*Listbox.selectForeground", p["on_accent"])
        self.option_add("*TCombobox*Listbox.font", self.f_small)

    def card(self, parent, **grid):
        outer = tk.Frame(parent, bg=self.pal["surface"], highlightbackground=self.pal["border"],
                         highlightthickness=1)
        outer.grid(**grid)
        body = ttk.Frame(outer, style="Card.TFrame", padding=(self.px(18), self.px(14)))
        body.pack(fill="both", expand=True)
        return body

    def listbox(self, parent, height):
        f = ttk.Frame(parent, style="Card.TFrame")
        lb = tk.Listbox(f, height=height, activestyle="none", exportselection=False, bd=0,
                        highlightthickness=0, bg=self.pal["surface2"], fg=self.pal["text"],
                        selectbackground=self.pal["accent"], selectforeground=self.pal["on_accent"],
                        font=self.f_small, selectborderwidth=0)
        sb = ttk.Scrollbar(f, command=lb.yview)
        lb.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        lb.pack(side="left", fill="both", expand=True)
        return f, lb

    # ---------- interface ----------
    def wlabel(self, parent, text, font=None, fg=None, bg=None):
        """Texto que quebra linha conforme a largura disponível e NÃO força largura mínima na janela."""
        p = self.pal
        lb = tk.Label(parent, text=text, font=font or self.f_small, fg=fg or p["muted"], bg=bg or p["surface"],
                      justify="left", anchor="w", width=1, wraplength=self.px(200), bd=0, padx=0, pady=0)

        def wrap(e):
            w = max(self.px(100), e.width - 2)
            if int(lb.cget("wraplength")) != w:
                lb.config(wraplength=w)
        lb.bind("<Configure>", wrap)
        return lb

    def hint(self, parent, text):
        return self.wlabel(parent, text)

    def fit_soon(self):
        if self._fit_job is None and not self.closing and not self._fit_lock:
            self._fit_job = self.after(120, self.fit_window)

    def fit_window(self):
        """O tamanho mínimo da janela é o que o conteúdo aberto precisa: nada fica escondido."""
        self._fit_job = None
        try:
            self.update_idletasks()
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            for _ in range(8):  # sem espaço na tela? fecha sozinho as seções de baixo (menos a que você abriu)
                self.update_idletasks()
                if self.winfo_reqheight() <= int(sh * 0.92):
                    break
                cands = [k for k in self.page_folds.get(self.cur_page, [])
                         if self.folds[k][1]["open"] and k != self.last_open]
                if not cands:
                    break
                self.folds[cands[-1]][2](False, False)
                self.auto_closed.append(cands[-1])
            self.update_idletasks()
            nw, nh = min(self.winfo_reqwidth(), int(sw * 0.96)), min(self.winfo_reqheight(), int(sh * 0.92))
            self.minsize(nw, nh)
            cw, ch = self.winfo_width(), self.winfo_height()
            if cw < nw or ch < nh:
                self.geometry(f"{max(cw, nw)}x{max(ch, nh)}")
            # voltou a ter espaço? reabre sozinho as seções que foram fechadas automaticamente
            mine = [k for k in self.auto_closed if k in self.page_folds.get(self.cur_page, [])]
            sig = (cw, ch, tuple(mine))
            if mine and sig != self._reopen_sig:
                self._reopen_sig = sig
                k = mine[-1]
                self._fit_lock = True
                try:
                    self.folds[k][2](True, False)
                    self.update_idletasks()
                    if self.winfo_reqheight() > min(self.winfo_height(), int(sh * 0.92)):
                        self.folds[k][2](False, False)
                    else:
                        self.auto_closed.remove(k)
                finally:
                    self._fit_lock = False
                if k not in self.auto_closed:
                    self.fit_soon()
        except tk.TclError:
            self._fit_lock = False

    def _build(self):
        p, px = self.pal, self.px
        Flow.hook = self.fit_soon
        top = winframe.build_bar(self)  # com a barra própria, os controles da janela ficam na mesma linha do cabeçalho
        if top:  # tudo numa linha só: marca | PT/EN, tutorial, celular | minimizar, maximizar, fechar
            brand = tk.Frame(top, bg=p["bg"])
            brand.pack(side="left", padx=(px(18), 0), pady=px(8))
            Logo(brand).pack(side="left", padx=(0, px(10)))
            tk.Label(brand, text=T("app_title"), font=self.f_title, bg=p["bg"], fg=p["text"]).pack(side="left")
            for wd, kw in ((Btn(top, text=T("btn_remote"), command=self.qr_window), dict(padx=(px(8), px(4)))),
                           (Btn(top, text=T("btn_tutorial"), command=self.open_tutorial), dict(padx=(px(8), 0)))):
                wd.pack(side="right", **kw)
            self.lang_sw = Segmented(top, [("pt", "PT"), ("en", "EN")], LANG["v"], command=self.apply_language,
                                     toggle=True, height=28)
            self.lang_sw.pack(side="right", padx=(px(8), 0))
            top.make_draggable()
        else:
            head = Flow(self, p["bg"], gap=px(10), vgap=px(6))
            head.pack(fill="x", padx=px(18), pady=(px(12), px(4)))
            brand = tk.Frame(head, bg=p["bg"])
            Logo(brand).pack(side="left", padx=(0, px(10)))
            tt = tk.Frame(brand, bg=p["bg"])
            tt.pack(side="left")
            tk.Label(tt, text=T("app_title"), font=self.f_title, bg=p["bg"], fg=p["text"]).pack(anchor="w")
            tk.Label(tt, text=T("subtitle"), font=self.f_small, bg=p["bg"], fg=p["muted"]).pack(anchor="w")
            head.add(brand)
            head.add(tk.Frame(head, bg=p["bg"], width=1, height=1), grow=True)
            self.lang_sw = Segmented(head, [("pt", "PT"), ("en", "EN")], LANG["v"], command=self.apply_language,
                                     toggle=True, height=28)
            head.add(self.lang_sw)
            head.add(Btn(head, text=T("btn_tutorial"), command=self.open_tutorial))
            head.add(Btn(head, text=T("btn_remote"), command=self.qr_window))

        bar = Flow(self, p["bg"], gap=px(10), vgap=px(6))
        bar.pack(fill="x", padx=px(18), pady=(px(2), px(6)))
        lab = tk.Frame(bar, bg=p["bg"])
        tk.Label(lab, text=T("lbl_playon"), font=self.f_small, bg=p["bg"], fg=p["muted"]).pack(side="left", padx=(0, px(8)))
        self.target_sw = Segmented(lab, [("cast", T("tgt_cast")), ("pc", T("tgt_pc"))], self.target,
                                   command=self.on_target)
        self.target_sw.pack(side="left")
        bar.add(lab)
        self.pill = Pill(bar)
        bar.add(self.pill)
        self.combo = ttk.Combobox(bar, state="readonly", width=24)
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.connect(self.combo.get()))
        bar.add(self.combo)
        bar.add(Btn(bar, text=T("btn_find"), command=self.discover))

        foot = tk.Frame(self, bg=p["bg"])
        foot.pack(side="bottom", fill="x", padx=px(18), pady=(0, px(8)))
        ff = Flow(foot, p["bg"], gap=px(6), vgap=px(4))
        ff.pack(fill="x")
        self.msg_line = ttk.Label(ff, text=T("ready"),
                                  style="Muted.TLabel", anchor="w", width=12)
        self.msg_line.bind("<Configure>", lambda e: self.msg_line.config(wraplength=max(100, e.width - 4)))
        ff.add(self.msg_line, grow=True)
        self.space_btn = Btn(ff, text="", style="Mini.TButton", command=self.goto_storage)
        ff.add(self.space_btn)
        ff.show(self.space_btn, False)  # só aparece quando a pasta passa de 50% do limite
        self.space_flow = ff
        ff.add(Btn(ff, text=T("btn_notice"), style="Mini.TButton", command=lambda: NoticeDialog(self)))
        self.det_btn = Btn(ff, text=T("details"), command=self.toggle_details)
        ff.add(self.det_btn)
        ff.add(Btn(ff, text=T("copy_log"), command=self.copy_log))
        self.box = tk.Text(foot, height=7, wrap="word", font=self.f_mono, bg=p["surface"], fg=p["text"],
                           relief="flat", bd=0, highlightthickness=1, highlightbackground=p["border"],
                           state="disabled", padx=8, pady=6)
        self.box_shown = False

        tabs = ttk.Frame(self, padding=(px(18), px(4), px(18), 0))
        tabs.pack(fill="x")
        self.tab_btns, self.tab_bars = {}, {}
        for key, txt in (("play", T("tab_play")), ("lists", T("tab_lists")), ("files", T("tab_files")),
                         ("set", T("tab_set"))):
            col = ttk.Frame(tabs)
            col.pack(side="left", padx=(0, px(6)))
            b = tk.Label(col, text=txt, font=self.f_head, cursor="hand2", bg=p["bg"], fg=p["muted"],
                         padx=px(12), pady=px(5))
            b.pack()
            bar = tk.Frame(col, height=max(2, px(3)), bg=p["bg"])
            bar.pack(fill="x")
            b.bind("<Button-1>", lambda e, k=key: self.show_page(k))
            self.tab_btns[key], self.tab_bars[key] = b, bar
        tk.Frame(self, height=1, bg=p["border"]).pack(fill="x", padx=px(18))

        self.pages = ttk.Frame(self, padding=(px(18), px(10), px(18), px(4)))
        self.pages.pack(fill="both", expand=True)
        self.pages.columnconfigure(0, weight=1)
        self.pages.rowconfigure(0, weight=1)
        self.page = {}
        for key in ("play", "lists", "files", "set"):
            fr = ttk.Frame(self.pages)
            fr.columnconfigure(0, weight=1)
            self.page[key] = fr
        for key, fn in (("play", self._page_play), ("lists", self._page_lists), ("files", self._page_files),
                        ("set", self._page_settings)):
            self._cur = key
            fn(self.page[key])
        self.show_page(self.cur_page if self.cur_page in self.page else "play")
        self.bind("<Configure>", lambda e: self.fit_soon() if e.widget is self else None)
        self.restore_state()
        self.fit_soon()
        winframe.raise_grips(self)

    def rebuild(self):
        """Refaz a tela inteira (troca de idioma, tema ou tamanho) sem perder o estado do programa."""
        try:
            link = self.link.get()
        except Exception:
            link = ""
        try:  # invisível durante a remontagem, para não aparecer pela metade
            self.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        for w in list(self.winfo_children()):
            w.destroy()
        self.tut = None
        self.folds, self.page_folds, self.auto_closed, self.last_open = {}, {}, [], None
        self.box_shown = False
        self.title(T("app_title"))
        self._style()
        self._build()
        if link:
            self.link.insert(0, link)
        try:
            self.fit_window()
            self.update_idletasks()
            self.attributes("-alpha", 1.0)
        except tk.TclError:
            pass

    def restore_state(self):
        """Preenche a tela recém-criada com o que o programa já sabe (fila, status, volume...)."""
        self.render_status()
        self.render_now()
        self.box.config(state="normal")
        self.box.insert("end", "".join(self.log_lines))
        self.box.config(state="disabled")
        self.render_msg_line()
        self.play_btn.config(icon="pause" if self.playing else "play")
        self.refresh_toggles()
        self.vol.set(self.vol_val)
        self.vol_lbl.config(text=f"{int(self.vol_val)}%")
        self.set_timeline(self.pos, self.dur_now or self.dur)
        self.bulk_btn.config(text=T("bulk_stop") if self.bulk else T("bulk_start"))
        self.q_lbl.config(text=T("queue_from", name=self.queue_name) if self.queue_name else "")
        self.fill_devices()
        if self.tracks:
            self.fill_list()
        self.refresh_lists()
        self.refresh_usage()

    def show_page(self, key):
        p = self.pal
        if self.cur_page == "files" and key != "files" and hasattr(self, "files_list"):
            self.save_files_ui()
        self.cur_page = key
        for k, fr in self.page.items():
            if k == key:
                fr.grid(row=0, column=0, sticky="nsew")
            else:
                fr.grid_remove()
        for k, b in self.tab_btns.items():
            on = k == key
            b.config(fg=p["accent"] if on else p["muted"])
            self.tab_bars[k].config(bg=p["accent"] if on else p["bg"])
        if key == "files" and hasattr(self, "files_list"):
            self.refresh_files()
            self.after(60, self.focus_files)
        self.fit_soon()

    def toggle_details(self):
        if self.box_shown:
            self.box.pack_forget()
        else:
            self.box.pack(fill="x", pady=(8, 0))
            self.box.see("end")
        self.box_shown = not self.box_shown
        self.det_btn.config(text=T("details"))
        self.fit_soon()

    def fold(self, parent, title, row, key, grow=False, flow=None, default_open=True):
        """Seção com seta: clique no título para abrir/fechar. Devolve (corpo, área extra do cabeçalho)."""
        p, px = self.pal, self.px
        outer = tk.Frame(parent, bg=p["surface"], highlightbackground=p["border"], highlightthickness=1)
        if flow is not None:
            flow.add(outer, grow=True)
        else:
            outer.grid(row=row, column=0, sticky="nsew" if grow else "ew", pady=(0, px(9)))
        outer.columnconfigure(0, weight=1)
        head = tk.Frame(outer, bg=p["surface"], cursor="hand2")
        head.grid(row=0, column=0, sticky="ew", padx=px(12), pady=(px(7), px(5)))
        arrow = Chevron(head, p["accent"], p["surface"])
        arrow.pack(side="left")
        lab = tk.Label(head, text=title, bg=p["surface"], fg=p["muted"], font=self.f_head)
        lab.pack(side="left")
        extra = tk.Frame(head, bg=p["surface"])
        extra.pack(side="right")
        body = ttk.Frame(outer, style="Card.TFrame", padding=(px(14), 0, px(14), px(10)))
        body.grid(row=1, column=0, sticky="nsew")
        st = {"open": not self.cfg.get("fold", {}).get(key, not default_open)}

        self.page_folds.setdefault(self._cur, []).append(key)

        def apply():
            if st["open"]:
                body.grid()
                arrow.config(text="▾")
            else:
                body.grid_remove()
                arrow.config(text="▸")
            if grow and flow is None:
                parent.rowconfigure(row, weight=1 if st["open"] else 0)
                outer.rowconfigure(1, weight=1 if st["open"] else 0)
            self.fit_soon()

        def setopen(o, save=True):
            st["open"] = o
            apply()
            if save:
                with self.cfg_lock:
                    self.cfg.setdefault("fold", {})[key] = not o
                    save_cfg(self.cfg)

        def toggle(_e=None):
            if key in self.auto_closed:
                self.auto_closed.remove(key)
            if not st["open"]:
                self.last_open = key
            setopen(not st["open"])
        for w in (head, arrow, lab):
            w.bind("<Button-1>", toggle)
        self.folds[key] = (toggle, st, setopen)
        apply()
        return body, extra

    def quals(self):
        return [(T("q_auto"), "auto"), ("360p", "360"), ("480p", "480"), ("720p HD", "720"),
                ("1080p Full HD", "1080"), ("1440p 2K*", "1440"), ("2160p 4K*", "2160")]

    def sleeps(self):
        return ([(T("sleep_off"), "0")] + [(T("sleep_n", n=n), str(n)) for n in (15, 30, 60, 90)]
                + [(T("sleep_end"), "end")])

    def _page_play(self, f):
        px, p = self.px, self.pal
        sf = p["surface"]
        c1, _ = self.fold(f, T("sec_add"), 0, "add")
        c1.columnconfigure(0, weight=1)
        rf = Flow(c1, sf, gap=px(6), vgap=px(6))
        rf.grid(row=0, column=0, sticky="ew")
        self.link = ttk.Entry(rf, font=self.f_small, width=16)
        self.link.bind("<Return>", lambda e: self.play_link(True))
        rf.add(self.link, grow=True)
        rf.add(Btn(rf, text=T("btn_playnow"), style="Accent.TButton", command=lambda: self.play_link(True)))
        rf.add(Btn(rf, text=T("btn_queue"), command=lambda: self.play_link(False)))
        rf.add(Btn(rf, text=T("btn_files"), command=self.add_files))
        qf = Flow(c1, sf, gap=px(6), vgap=px(6))
        qf.grid(row=1, column=0, sticky="ew", pady=(px(6), 0))
        qf.add(ttk.Label(qf, text=T("lbl_mylists"), style="CardMuted.TLabel"))
        self.pl_quick = ttk.Combobox(qf, state="readonly", width=22)
        qf.add(self.pl_quick, grow=True)
        qf.add(Btn(qf, text=T("btn_open_pl"), command=self.open_quick_pl))
        self.hint(c1, T("hint_add")).grid(row=2, column=0, sticky="ew", pady=(px(4), 0))

        c2, _ = self.fold(f, T("sec_now"), 1, "now")
        c2.columnconfigure(0, weight=1)
        self.now_title = self.wlabel(c2, T("nothing"), font=self.f_big, fg=p["text"])
        self.now_title.grid(row=0, column=0, sticky="ew")
        self.now_sub = self.wlabel(c2, T("now_hint"))
        self.now_sub.grid(row=1, column=0, sticky="ew")
        tl = ttk.Frame(c2, style="Card.TFrame")
        tl.grid(row=2, column=0, sticky="ew", pady=(px(6), 0))
        tl.columnconfigure(1, weight=1)
        self.t_now = ttk.Label(tl, text="0:00", style="CardMuted.TLabel", width=7)
        self.t_now.grid(row=0, column=0)
        self.tl = Slider(tl, self.pal, self.u, command=self.on_tl,
                         press=lambda: setattr(self, "dragging", True), release=self.tl_release, width=60)
        self.tl.grid(row=0, column=1, sticky="ew")
        self.t_total = ttk.Label(tl, text="0:00", style="CardMuted.TLabel", width=7, anchor="e")
        self.t_total.grid(row=0, column=2)

        tr = Flow(c2, sf, gap=px(8), vgap=px(8), align="center")
        tr.grid(row=3, column=0, sticky="ew", pady=(px(8), px(6)))
        mkb = lambda icon, st, cmd: Btn(tr, icon=icon, style=st, command=cmd)
        self.btn_shuf = mkb("shuffle", "Toggle.TButton", lambda: self.set_shuffle(not self.shuffle_on))
        self.btn_prev = mkb("prev", "Icon.TButton", self.prev_track)
        self.btn_back = mkb("back10", "Skip.TButton", lambda: self.skip(-10))
        self.play_btn = mkb("play", "Play.TButton", self.toggle_play)
        self.btn_fwd = mkb("fwd10", "Skip.TButton", lambda: self.skip(10))
        self.btn_next = mkb("next", "Icon.TButton", self.next_track)
        self.btn_rep = mkb("repeat", "Toggle.TButton", lambda: self.set_repeat(not self.repeat_on))
        self.btn_stop = mkb("stop", "Icon.TButton", self.stop)
        for b in (self.btn_shuf, self.btn_prev, self.btn_back, self.play_btn, self.btn_fwd, self.btn_next,
                  self.btn_rep, self.btn_stop):
            tr.add(b)
        self.hint(c2, T("hint_ctl")).grid(row=4, column=0, sticky="ew")

        bf = Flow(c2, sf, gap=px(18), vgap=px(8))
        bf.grid(row=5, column=0, sticky="ew", pady=(px(8), 0))
        g1 = tk.Frame(bf, bg=sf)
        vi = tk.Canvas(g1, width=px(28), height=px(28), bg=sf, highlightthickness=0, bd=0)
        draw_icon(vi, "volume", px(14), px(14), px(10), p["muted"])
        vi.pack(side="left", padx=(0, px(4)))
        self.vol = Slider(g1, self.pal, self.u, command=self.on_vol_move,
                          press=lambda: setattr(self, "vol_drag", True), release=self.on_vol_release,
                          height=22, width=130)
        self.vol.set(50)
        self.vol.pack(side="left")
        self.vol_lbl = ttk.Label(g1, text="50%", style="CardMuted.TLabel", width=5)
        self.vol_lbl.pack(side="left")
        bf.add(g1)
        g2 = tk.Frame(bf, bg=sf)
        ttk.Label(g2, text=T("lbl_quality"), style="CardMuted.TLabel").pack(side="left", padx=(0, px(5)))
        self.qual_cb = ttk.Combobox(g2, state="readonly", width=13, values=[a for a, _ in self.quals()])
        self.qual_cb.set(next((a for a, v in self.quals() if v == str(CFGS["quality"])), T("q_auto")))
        self.qual_cb.pack(side="left")
        self.qual_cb.bind("<<ComboboxSelected>>",
                          lambda e: self.set_quality(dict(self.quals())[self.qual_cb.get()]))
        bf.add(g2)
        self.sleep_cb = ttk.Combobox(bf, state="readonly", width=19, values=[a for a, _ in self.sleeps()])
        self.sleep_cb.set(T("sleep_off"))
        self.sleep_cb.bind("<<ComboboxSelected>>", lambda e: self.set_sleep(dict(self.sleeps())[self.sleep_cb.get()]))
        bf.add(self.sleep_cb)

        c3, ex = self.fold(f, T("sec_queue"), 2, "queue", grow=True)
        c3.columnconfigure(0, weight=1)
        c3.rowconfigure(0, weight=1)
        self.save_btn = Btn(ex, text=T("btn_save_queue"), command=self.save_queue)
        self.save_btn.pack(side="right")
        self.bulk_btn = Btn(ex, text=T("bulk_start"), command=self.toggle_bulk)
        self.bulk_btn.pack(side="right", padx=(0, px(6)))
        self.dl_lbl = ttk.Label(ex, text="", style="CardMuted.TLabel")
        self.dl_lbl.pack(side="right", padx=px(10))
        self.q_lbl = ttk.Label(ex, text="", style="CardMuted.TLabel")
        self.q_lbl.pack(side="right")
        lf, self.lst = self.listbox(c3, 4)
        lf.grid(row=0, column=0, sticky="nsew")
        self.lst.bind("<Double-Button-1>", lambda e: self.pick())
        self.lst.bind("<Return>", lambda e: (self.pick(), "break")[-1])
        self.lst.bind("<Delete>", lambda e: (self.remove_queue_item(), "break")[-1])
        self.hint(c3, T("hint_queue")).grid(row=1, column=0, sticky="ew", pady=(px(6), 0))

    def field(self, c, label, hint=""):
        px = self.px
        fr = ttk.Frame(c, style="Card.TFrame")
        fr.pack(fill="x", pady=(px(3), px(7)))
        ttk.Label(fr, text=label, style="Card.TLabel", font=self.f_head).pack(anchor="w")
        if hint:
            self.hint(fr, hint).pack(anchor="w", fill="x")
        ctl = ttk.Frame(fr, style="Card.TFrame")
        ctl.pack(fill="x", pady=(px(4), 0))
        return ctl

    def _page_settings(self, f):
        px = self.px
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)
        box = ScrollBox(f, self.pal["bg"], height=px(300))
        box.grid(row=0, column=0, sticky="nsew")
        inner = box.inner
        inner.columnconfigure(0, weight=1)
        rows = [0]

        def sec(title, key, op=True):  # uma coluna só: cada seção fica embaixo da anterior
            rows[0] += 1
            return self.fold(inner, title, rows[0], key, default_open=op)[0]

        def spin(ctl, var, a, b, inc):
            sp = ttk.Spinbox(ctl, from_=a, to=b, increment=inc, width=8, textvariable=var,
                             command=self.apply_settings)
            sp.pack(side="left")
            sp.bind("<Return>", self.apply_settings)
            sp.bind("<FocusOut>", self.apply_settings)

        # 1) TV / conexão: o que mais se usa
        c = sec(T("sec_set_conn"), "s_conn")
        ctl = self.field(c, T("f_device"), T("h_device"))
        lf, self.dev_list = self.listbox(ctl, 3)
        lf.pack(fill="x")
        self.dev_list.bind("<Double-Button-1>", lambda e: self.connect_selected())
        bb = Flow(ctl, self.pal["surface"], gap=px(6), vgap=px(6))
        bb.pack(fill="x", pady=(px(6), 0))
        bb.add(Btn(bb, text=T("b_connect"), style="Accent.TButton", command=self.connect_selected))
        bb.add(Btn(bb, text=T("b_research"), command=self.discover))

        # 2) Reprodução
        c = sec(T("sec_set_play"), "s_play")
        ctl = self.field(c, T("f_mode"), T("h_mode"))
        self.var_mode = tk.StringVar(value=CFGS["mode"])
        ttk.Radiobutton(ctl, text=T("m_video"), variable=self.var_mode, value="video",
                        command=self.apply_settings).pack(side="left", padx=(0, px(14)))
        ttk.Radiobutton(ctl, text=T("m_audio"), variable=self.var_mode, value="audio",
                        command=self.apply_settings).pack(side="left")
        ctl = self.field(c, T("f_screen"), T("h_screen"))
        self.var_screen = tk.StringVar(value="cover")
        ttk.Radiobutton(ctl, text=T("s_cover"), variable=self.var_screen, value="cover",
                        command=self.apply_settings).pack(side="left")
        self.var_look = tk.StringVar(value=str(self.lookahead))
        spin(self.field(c, T("f_look"), T("h_look")), self.var_look, 1, 20, 1)

        # Legendas e som
        c = sec(T("sec_set_media"), "s_media")
        ctl = self.field(c, T("f_subs"), T("h_subs"))
        self.var_subs = tk.StringVar(value=CFGS.get("subs", "off"))
        for val, key in (("off", "sub_off"), ("pt", "sub_pt"), ("en", "sub_en")):
            ttk.Radiobutton(ctl, text=T(key), variable=self.var_subs, value=val,
                            command=self.apply_settings).pack(side="left", padx=(0, px(14)))
        ctl = self.field(c, T("f_norm"), T("h_norm"))
        self.var_norm = tk.BooleanVar(value=bool(CFGS.get("norm")))
        ttk.Checkbutton(ctl, text=T("ck_norm"), variable=self.var_norm, command=self.apply_settings,
                        style="Card.TCheckbutton").pack(side="left")
        ctl = self.field(c, T("f_hevc"), T("h_hevc"))
        self.var_hevc = tk.BooleanVar(value=bool(CFGS.get("hevc")))
        ttk.Checkbutton(ctl, text=T("ck_hevc"), variable=self.var_hevc, command=self.apply_settings,
                        style="Card.TCheckbutton").pack(side="left")

        # 3) Armazenamento
        c = sec(T("sec_set_store"), "s_store")
        ctl = self.field(c, T("f_dir"), T("h_dir"))
        self.var_dir = tk.StringVar(value=CFGS["cache"])
        ttk.Entry(ctl, textvariable=self.var_dir, state="readonly", width=18).pack(fill="x")
        bb = ttk.Frame(ctl, style="Card.TFrame")
        bb.pack(fill="x", pady=(px(4), 0))
        Btn(bb, text=T("b_choose"), command=self.choose_dir).pack(side="left")
        Btn(bb, text=T("b_open"), command=self.open_dir).pack(side="left", padx=(px(6), 0))
        self.var_max = tk.StringVar(value=str(CFGS["max_gb"]).rstrip("0").rstrip("."))
        spin(self.field(c, T("f_limit"), T("h_limit")), self.var_max, 0, 2000, 1)
        ctl = self.field(c, T("f_usage"), T("h_usage"))
        self.usage_lbl = self.wlabel(ctl, T("usage_calc"), fg=self.pal["text"])
        self.usage_lbl.pack(fill="x", pady=(0, px(4)))
        self.space_bar = tk.Canvas(ctl, height=px(8), bg=self.pal["surface"], highlightthickness=0, bd=0)
        self.space_bar.pack(fill="x", pady=(0, px(6)))
        self.space_bar.bind("<Configure>", lambda e: self.draw_space_bar())
        bb = Flow(ctl, self.pal["surface"], gap=px(6), vgap=px(6))
        bb.pack(fill="x")
        bb.add(Btn(bb, text=T("b_clean"), command=self.clean_cache))
        bb.add(Btn(bb, text=T("b_delvids"), command=self.delete_videos))

        # 4) Idioma e aparência (mudam na hora)
        c = sec(T("sec_set_look"), "s_look")
        ctl = self.field(c, T("f_lang"), T("h_lang"))
        self.var_lang = tk.StringVar(value=LANGS[LANG["v"]])
        cb = ttk.Combobox(ctl, state="readonly", width=20, textvariable=self.var_lang, values=list(LANGS.values()))
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", self.change_lang)
        ctl = self.field(c, T("f_theme"), T("h_theme"))
        self.var_theme = tk.StringVar(value=T("th_" + self.theme))
        th = ttk.Combobox(ctl, state="readonly", width=14, textvariable=self.var_theme,
                          values=[T("th_" + k) for k in PALETTES])
        th.pack(side="left")
        th.bind("<<ComboboxSelected>>", self.apply_settings)
        ctl = self.field(c, T("f_size"), T("h_size"))
        self.var_size = tk.StringVar(value=T("sz_" + self.size_name))
        sz = ttk.Combobox(ctl, state="readonly", width=14, textvariable=self.var_size,
                          values=[T("sz_" + k) for k in SIZES])
        sz.pack(side="left")
        sz.bind("<<ComboboxSelected>>", self.apply_settings)

        # 5) Avançado: só mexa se precisar (começa fechado)
        c = sec(T("sec_set_adv"), "s_adv", False)
        ctl = self.field(c, T("f_ip"), T("h_ip"))
        self.ip = ttk.Entry(ctl, width=16)
        self.ip.insert(0, self.cfg.get("ip", ""))
        self.ip.pack(side="left")
        Btn(ctl, text=T("b_ip"), command=self.by_ip).pack(side="left", padx=(px(8), 0))
        ctl = self.field(c, T("f_cookies"), T("h_cookies"))
        self.var_ck = tk.BooleanVar(value=bool(CFGS.get("cookies_file")))
        ttk.Checkbutton(ctl, text=T("ck_use"), variable=self.var_ck, command=self.toggle_cookies,
                        style="Card.TCheckbutton").pack(side="left")
        self.var_native = tk.BooleanVar(value=bool(self.cfg.get("native_frame")))
        ttk.Checkbutton(self.field(c, T("f_frame"), T("h_frame")), text=T("ck_frame"), variable=self.var_native,
                        command=self.toggle_frame, style="Card.TCheckbutton").pack(side="left")
        self.var_adj = tk.StringVar(value=str(self.adjust))
        spin(self.field(c, T("f_adj"), T("h_adj")), self.var_adj, -2, 3, 0.5)
        ctl = self.field(c, T("f_backup"), T("h_backup"))
        Btn(ctl, text=T("bk_export"), command=self.export_cfg).pack(side="left")
        Btn(ctl, text=T("bk_import"), command=self.import_cfg).pack(side="left", padx=(px(8), 0))

        # 6) Ajuda: sempre a última seção da lista
        c = sec(T("sec_set_help"), "s_help")
        ctl = self.field(c, T("f_keys"), T("h_keys"))
        Btn(ctl, text=T("b_keys"), command=self.show_keys).pack(side="left")
        ctl = self.field(c, T("f_welcome"), T("h_welcome"))
        Btn(ctl, text=T("b_welcome"), command=self.show_welcome).pack(side="left")

    def _page_lists(self, f):
        px, sf = self.px, self.pal["surface"]
        c, _ = self.fold(f, T("sec_resume"), 0, "resume")
        c.columnconfigure(0, weight=1)
        self.resume_lbl = self.wlabel(c, "", fg=self.pal["text"])
        self.resume_lbl.grid(row=0, column=0, sticky="ew", pady=(0, px(6)))
        self.resume_btn = Btn(c, text=T("btn_resume"), style="Accent.TButton",
                                     command=lambda: self.bg(self.resume_session))
        self.resume_btn.grid(row=1, column=0, sticky="w")

        c, _ = self.fold(f, T("sec_playlists"), 1, "playlists", grow=True)
        c.columnconfigure(0, weight=1)
        c.rowconfigure(1, weight=1)
        c.rowconfigure(4, weight=1)
        self.hint(c, T("pl_hint")).grid(row=0, column=0, sticky="ew", pady=(0, px(6)))
        lf, self.pl_list = self.listbox(c, 4)
        lf.grid(row=1, column=0, sticky="nsew")
        self.pl_list.bind("<<ListboxSelect>>", lambda e: self.pl_selected())
        self.pl_list.bind("<Double-Button-1>", lambda e: self.open_playlist())
        self.pl_list.bind("<Return>", lambda e: (self.open_playlist(), "break")[-1])
        self.pl_list.bind("<Delete>", lambda e: (self.delete_playlist(), "break")[-1])
        self.pl_list.bind("<F2>", lambda e: (self.rename_playlist(), "break")[-1])
        bf = Flow(c, sf, gap=px(6), vgap=px(6))
        bf.grid(row=2, column=0, sticky="ew", pady=(px(8), 0))
        for txt, cmd, st in ((T("pl_play"), self.open_playlist, "Accent.TButton"),
                             (T("pl_enqueue"), self.enqueue_playlist, "TButton"),
                             (T("pl_new"), self.new_playlist, "TButton"),
                             (T("pl_save_q"), self.save_playlist, "TButton"),
                             (T("pl_rename"), self.rename_playlist, "TButton"),
                             (T("pl_delete"), self.delete_playlist, "TButton")):
            bf.add(Btn(bf, text=txt, style=st, command=cmd))
        self.pl_items_lbl = self.wlabel(c, T("pl_none_sel"), font=self.f_head, fg=self.pal["text"])
        self.pl_items_lbl.grid(row=3, column=0, sticky="ew", pady=(px(10), px(4)))
        lf2, self.pl_items = self.listbox(c, 4)
        self.pl_items.bind("<Delete>", lambda e: (self.remove_pl_item(), "break")[-1])
        lf2.grid(row=4, column=0, sticky="nsew")
        af = Flow(c, sf, gap=px(6), vgap=px(6))
        af.grid(row=5, column=0, sticky="ew", pady=(px(8), 0))
        self.pl_link = ttk.Entry(af, font=self.f_small, width=16)
        self.pl_link.bind("<Return>", lambda e: self.add_link_to_playlist())
        af.add(self.pl_link, grow=True)
        af.add(Btn(af, text=T("pl_add_link"), command=self.add_link_to_playlist))
        af.add(Btn(af, text=T("pl_rm_item"), command=self.remove_pl_item))

    def _page_files(self, f):
        px, sf = self.px, self.pal["surface"]
        c, extra = self.fold(f, T("sec_files"), 0, "files", grow=True)
        c.columnconfigure(0, weight=1)
        c.rowconfigure(3, weight=1)
        self.hint(c, T("files_hint")).grid(row=0, column=0, sticky="ew", pady=(0, px(6)))
        tf = tk.Frame(c, bg=sf)
        tf.grid(row=1, column=0, sticky="ew", pady=(0, px(6)))
        tf.columnconfigure(1, weight=1)
        ui = self.cfg.get("files_ui") or {}
        self.var_fq = tk.StringVar()
        tk.Label(tf, text=T("files_search"), bg=sf, fg=self.pal["muted"], font=self.f_small).grid(
            row=0, column=0, padx=(0, px(6)))
        self.files_q = ttk.Entry(tf, textvariable=self.var_fq, font=self.f_small, width=12)
        self.files_q.grid(row=0, column=1, sticky="ew")
        self.var_fq.trace_add("write", lambda *a: self._show_files())
        self.files_q.bind("<Escape>", lambda e: (self.var_fq.set(""), self.files_list.focus_set(), "break")[-1])
        self.files_q.bind("<Down>", lambda e: (self.files_list.focus_set(), "break")[-1])
        self.files_q.bind("<Return>", lambda e: (self.files_list.focus_set(), "break")[-1])
        self.sort_names = [(k, T("files_sort_" + k)) for k in ("new", "name", "size")]
        self.var_fs = tk.StringVar(value=dict(self.sort_names).get(ui.get("sort"), self.sort_names[0][1]))
        sc = ttk.Combobox(tf, textvariable=self.var_fs, values=[v for _, v in self.sort_names], state="readonly",
                          width=16, font=self.f_small)
        sc.grid(row=0, column=2, padx=(px(6), 0))
        sc.bind("<<ComboboxSelected>>", lambda e: (self._show_files(), self.files_list.focus_set()))
        self.files_lbl = self.wlabel(c, "", fg=self.pal["text"])
        self.files_lbl.grid(row=2, column=0, sticky="ew", pady=(0, px(4)))
        lf, self.files_list = self.listbox(c, 8)
        lf.grid(row=3, column=0, sticky="nsew")
        L = self.files_list
        L.config(selectmode="extended")
        L.bind("<Double-Button-1>", lambda e: self.play_files())
        L.bind("<Return>", lambda e: (self.play_files(), "break")[-1])
        L.bind("<Delete>", lambda e: self.delete_files_sel())
        L.bind("<F2>", lambda e: self.rename_file())
        L.bind("<Control-a>", lambda e: (L.selection_set(0, "end"), "break")[-1])
        L.bind("<Control-A>", lambda e: (L.selection_set(0, "end"), "break")[-1])
        bf = Flow(c, sf, gap=px(6), vgap=px(6))
        bf.grid(row=4, column=0, sticky="ew", pady=(px(8), 0))
        for txt, cmd, st in ((T("files_play"), self.play_files, "Accent.TButton"),
                             (T("files_add"), lambda: self.play_files(add=True), "TButton"),
                             (T("files_rename"), self.rename_file, "TButton"),
                             (T("files_del"), self.delete_files_sel, "TButton"),
                             (T("files_del_all"), self.delete_files_all, "TButton"),
                             (T("files_folder"), self.open_files_folder, "TButton"),
                             (T("files_refresh"), self.refresh_files, "TButton")):
            bf.add(Btn(bf, text=txt, style=st, command=cmd))
        self.files_data, self.files_view = [], []
        self.files_sig = None
        self.files_want = ui.get("sel")
        self.refresh_files()

    def refresh_files(self):
        """Lê a pasta fora da tela principal (pode ter muitos arquivos) e só então atualiza a lista."""
        if getattr(self, "files_busy", False):
            return
        self.files_busy = True

        def work():
            try:
                data = downloaded_files()
            except Exception:
                log(traceback.format_exc())
                data = []
            self.ui(lambda: self._fill_files(data))
        threading.Thread(target=work, daemon=True).start()

    def _fill_files(self, data):
        self.files_busy = False
        try:
            if not self.files_list.winfo_exists():
                return
        except Exception:
            return
        sig = [(x["path"], x["size"], x["title"]) for x in data]
        if sig == self.files_sig:
            return
        self.files_sig = sig
        self.files_data = data
        self._show_files()

    def _sort_key(self):
        cur = self.var_fs.get()
        return next((k for k, v in self.sort_names if v == cur), "new")

    def _show_files(self, keep=None):
        """Mostra a lista já filtrada (busca) e ordenada, mantendo a seleção e a posição."""
        L = self.files_list
        try:
            if not L.winfo_exists():
                return
        except Exception:
            return
        if keep is None:
            keep = [self.files_view[i]["path"] for i in L.curselection() if i < len(self.files_view)]
            if not keep and self.files_want:
                keep = [self.files_want]
        self.files_want = None
        top = L.yview()[0]
        q = self.var_fq.get().strip().lower()
        view = [x for x in self.files_data if not q or q in x["title"].lower()]
        k = self._sort_key()
        if k == "name":
            view.sort(key=lambda x: x["title"].lower())
        elif k == "size":
            view.sort(key=lambda x: -x["size"])
        self.files_view = view
        L.delete(0, "end")
        for x in view:
            kind = T("files_kind_a") if x["audio"] else T("files_kind_v")
            L.insert("end", f"{x['title']}   ·   {kind}   ·   {fmt_size(x['size'])}")
        for i, x in enumerate(view):
            if x["path"] in keep:
                L.selection_set(i)
        L.yview_moveto(top)
        if view and not L.curselection() and self.cur_page == "files":  # sempre há um item marcado: o teclado já funciona
            L.selection_set(0)
            L.activate(0)
        tot = sum(x["size"] for x in self.files_data)
        if not self.files_data:
            self.files_lbl.config(text=T("files_empty"))
        elif q:
            self.files_lbl.config(text=T("files_found", n=len(view), t=len(self.files_data)))
        else:
            self.files_lbl.config(text=T("files_count", n=len(self.files_data), s=fmt_size(tot)))

    def focus_files(self):
        """Ao abrir a aba, o teclado já funciona: foco na lista e primeiro item marcado."""
        try:
            L = self.files_list
            if self.focus_get() is not self.files_q:
                L.focus_set()
            if not L.curselection() and L.size():
                L.selection_set(0)
                L.activate(0)
        except Exception:
            pass

    def save_files_ui(self):
        try:
            sel = [self.files_view[i]["path"] for i in self.files_list.curselection() if i < len(self.files_view)]
            ui = {"sort": self._sort_key(), "sel": sel[0] if sel else None}
        except Exception:
            return
        if ui != self.cfg.get("files_ui"):
            self.cfg["files_ui"] = ui
            with self.cfg_lock:
                save_cfg(self.cfg)

    def _files_selected(self):
        sel = [self.files_view[i] for i in self.files_list.curselection() if i < len(self.files_view)]
        if not sel:
            self.msg(T("files_pick"))
        return sel

    def play_files(self, add=False):
        sel = self._files_selected()
        if not sel or not self.mc():
            return
        new = [{"title": x["title"], "path": x["path"]} for x in sel]
        self.bg(lambda: self.add_tracks(new, not add))

    def in_use(self):
        return [self.cur_path] if (self.armed or self.playing) and self.cur_path else []

    def _after_files_change(self, msg):
        self.msg(msg)
        self.files_sig = None
        self.refresh_files()
        self.refresh_usage()

    def _do_delete(self, sel):
        items = []
        for x in sel:
            items.append((x["path"], x["size"], x["mtime"]))
            if x["json"]:
                items.append((x["json"], 0, 0))
        keep = self.in_use()
        n, size, kept, errs = delete_files(items, keep=keep)
        done = len([1 for x in sel if not os.path.exists(x["path"])])
        for x in sel:  # arquivo em uso ficou: o de controle dele também
            if os.path.exists(x["path"]) and x["json"] and not os.path.exists(x["json"]):
                try:
                    with open(x["json"], "w", encoding="utf-8") as f:
                        json.dump({"path": x["path"], "title": x["title"], "ctype": ctype_for(x["path"], x["audio"])},
                                  f, ensure_ascii=False)
                except OSError:
                    pass
        if kept:
            self.msg(T("files_inuse"))
        if errs:
            self.msg(T("files_del_err", e=errs[0][:120]))
        self._after_files_change(T("files_del_done", n=done, s=fmt_size(size)))

    def delete_files_sel(self):
        sel = self._files_selected()
        if not sel:
            return
        total = sum(x["size"] for x in sel)
        if not dialogs.confirm(self, T("delv_title"), T("files_del_ask", n=len(sel), s=fmt_size(total), nl="\n\n"),
                               yes=T("files_del"), default_no=True):
            return
        top, i0 = self.files_list.yview()[0], (self.files_list.curselection() or (0,))[0]
        self._do_delete(sel)
        self.files_want = None
        self.after(300, lambda: self._select_near(i0, top))

    def _select_near(self, i, top):
        """Depois de excluir, a seleção vai para o item seguinte (o teclado continua de onde parou)."""
        try:
            L = self.files_list
            if L.size() and not L.curselection():
                i = min(i, L.size() - 1)
                L.selection_set(i)
                L.activate(i)
                L.see(i)
        except Exception:
            pass

    def delete_files_all(self):
        mine = [x for x in self.files_data if x["json"] or x["id"]]  # só o que o programa baixou
        if not mine:
            self.msg(T("delv_none"))
            return
        total = sum(x["size"] for x in mine)
        if not dialogs.confirm(self, T("files_del_all_t"), T("files_del_all_ask", n=len(mine), s=fmt_size(total),
                                                             nl="\n\n"),
                               yes=T("files_del_all"), default_no=True):
            return
        self._do_delete(mine)

    def rename_file(self):
        sel = self._files_selected()
        if not sel:
            return
        if len(sel) > 1:
            self.msg(T("files_one"))
            return
        x = sel[0]
        if os.path.normcase(os.path.abspath(x["path"])) in {os.path.normcase(os.path.abspath(k)) for k in self.in_use()}:
            self.msg(T("files_rename_busy"))
            return
        name = dialogs.ask_text(self, T("files_rename_t"), T("files_rename_q"), x["title"])
        if not name or name == x["title"]:
            return
        try:
            new = rename_download(x, name)
        except Exception as e:
            self.msg(T("files_rename_err", e=str(e)[:150]))
            return
        self._repath(x["path"], new, name)
        self.files_want = new
        self._after_files_change(T("files_renamed", name=name))

    def _repath(self, old, new, title):
        """Quem apontava para o arquivo antigo (fila, playlists, lembretes) passa a apontar para o novo."""
        def fix(items):
            for t in items or []:
                if isinstance(t, dict) and t.get("path") == old:
                    t["path"], t["title"] = new, title
        fix(self.tracks)
        fix(self.orig)
        for pl in self.cfg.get("playlists", {}).values():
            fix(pl)
        fix((self.cfg.get("session") or {}).get("tracks"))
        for k in [k for k, v in self.cache.items() if v.get("path") == old]:
            self.cache.pop(k, None)
        if self.cur_path == old:
            self.cur_path = new
        self._save_pls()
        self.ui(self.fill_list)

    def open_files_folder(self):
        self.open_dir()

    # ---------- fila de atualizações da tela (seguro entre threads) ----------
    def ui(self, fn):
        self.q.put(fn)

    def drain(self):
        try:
            while True:
                self.q.get_nowait()()
        except queue.Empty:
            pass
        except Exception:
            log(traceback.format_exc())
        if not self.closing:
            self.after(100, self.drain)

    def bg(self, fn):
        def run():
            try:
                fn()
            except Exception as e:
                log(traceback.format_exc())
                self.msg(T("err_unexpected", e=e))
        threading.Thread(target=run, daemon=True).start()

    def msg(self, text):
        log(text)
        text = str(text)
        self.last_msg = text[:200]
        bad = text.startswith(BAD_PREFIX)
        line = time.strftime("%H:%M:%S  ") + text + "\n"
        self.log_lines = (self.log_lines + [line])[-400:]
        self.msg_view = ((text.splitlines() or [""])[0][:220], bad)

        def f():
            self.box.config(state="normal")
            self.box.insert("end", line)
            self.box.see("end")
            self.box.config(state="disabled")
            self.render_msg_line()
        self.ui(f)

    def render_msg_line(self):
        txt, bad = self.msg_view or (T("ready"), False)
        self.msg_line.config(text=txt, foreground=self.pal["bad"] if bad else self.pal["muted"])

    def copy_log(self):
        self.clipboard_clear()
        self.clipboard_append(self.box.get("1.0", "end"))
        self.msg(T("log_copied"))

    def set_status(self, key, color, **kw):
        """key = texto do status na tabela de idiomas. Online/Offline refletem a conexão real."""
        self.status_state = (key, kw, color)
        self.ui(self.render_status)

    def render_status(self):
        key, kw, color = self.status_state
        self.pill.set(T(key, **kw), self.pal[COLORMAP.get(color, "muted")])

    def set_online(self, ok):
        self.tv_online = ok
        if self.target == "pc":
            self.set_status("st_pc", "green")
            return
        name = self.cur_dev
        if ok:
            self.set_status("st_online_name" if name else "st_online", "green", name=name)
        else:
            self.set_status("st_offline", "red")

    # ---------- Chromecast ----------
    def prepare(self):
        prune()
        update_ytdlp()
        self.get_tools()
        if self.target == "pc" and not self.cast:
            self.cast = self.get_pcdev()
            self.set_status("st_pc", "green")

    def get_pcdev(self):
        if not self.pcdev:
            self.get_tools()
            self.pcdev = PCDevice(lambda: f"http://127.0.0.1:{self.remote.port}/pc?k={self.token}")
            self.pcdev.media_controller.register_status_listener(Watcher(self))
        return self.pcdev

    def get_tools(self):
        if not self.tools:
            self.msg(T("prep_tools"))
            self.tools = ensure_tools()
            self.msg(T("tools_ready"))
        if not self.server:
            self.server = FileServer()
        if not self.remote:
            self.remote = RemoteServer(self)
        return self.tools

    def stop_browser(self):
        if self.browser:
            try:
                self.browser.stop_discovery()
            except Exception:
                pass
            self.browser = None

    def direct(self, ip):
        import uuid
        import pychromecast
        return pychromecast.get_chromecast_from_host((ip, 8009, uuid.uuid4(), None, None))

    def ensure_deps(self):
        try:
            import pychromecast  # noqa
            return True
        except Exception as e:
            self.msg(T("missing_dep", e=e))
        try:
            pip_install("pychromecast")
            import pychromecast  # noqa
            return True
        except Exception as e:
            self.msg(T("dep_fail", e=e))
            return False

    def discover(self):
        self.set_status("st_searching", "orange")
        self.bg(self.discover_work)

    def discover_work(self):
        if not self.ensure_deps():
            self.set_status("st_missing", "red")
            return
        import pychromecast
        self.stop_browser()
        ip = self.cfg.get("ip", "").strip()
        casts, hosts = [], ([ip] if ip else [])
        if not hosts:
            try:
                casts, self.browser = pychromecast.get_chromecasts(timeout=6)
            except Exception:
                log("busca automatica falhou:\n" + traceback.format_exc())
            if not casts:
                self.set_status("st_scanning", "orange")
                hosts = scan_chromecasts()
        err = ""
        for h in hosts:
            try:
                casts.append(self.direct(h))
            except Exception as e:
                err = str(e)
                log(f"direto {h} falhou:\n" + traceback.format_exc())
        self.devices = {}
        for c in casts:
            try:
                nm = c.name or f"Chromecast ({c.cast_info.host})"
            except Exception:
                nm = "Chromecast"
            self.devices[nm] = c
        names = sorted(self.devices)
        self.ui(self.fill_devices)
        if not names:
            self.set_status("st_offline", "red")
            self.msg(T("not_found_help", err=T("err_prefix", e=err) if err else ""))
            return
        want = self.cfg.get("last") if self.cfg.get("last") in names else names[0]
        self.ui(lambda: self.combo.set(want))
        self.connect(want)

    def fill_devices(self):
        names = sorted(self.devices)
        self.combo.config(values=names)
        self.combo.set(self.cur_dev if self.cur_dev in self.devices else "")
        self.dev_list.delete(0, "end")
        for n in names:
            self.dev_list.insert("end", n + ("  " + T("dev_current") if (n == self.cur_dev and self.cast) else ""))
        if not names:
            self.dev_list.insert("end", T("dev_none"))

    def connect_selected(self):
        sel = self.dev_list.curselection()
        names = sorted(self.devices)
        if sel and sel[0] < len(names):
            self.connect(names[sel[0]])
        else:
            self.msg(T("dev_pick"))

    def watch_connection(self, ok):
        """Se a TV cair, tenta reconectar poucas vezes (com espera crescente) em vez de insistir sem parar."""
        now = time.time()
        if ok:
            self.off_since, self.retry_n, self.next_retry, self.gave_up = None, 0, 0, False
            return
        if self.off_since is None:
            self.off_since, self.next_retry = now, now + 12
        if self.retry_n < 5 and now >= self.next_retry and not self.reconnecting:
            self.retry_n += 1
            self.next_retry = now + (15, 30, 60, 120, 240)[self.retry_n - 1]
            self.bg(self.reconnect)
        elif self.retry_n >= 5 and not self.gave_up and now >= self.next_retry:
            self.gave_up = True
            self.msg(T("reconnect_fail"))

    def reconnect(self):
        if self.reconnecting or not self.chromecast or self.target != "cast":
            return
        self.reconnecting = True
        try:
            name, old = self.cur_dev, self.chromecast
            self.msg(T("reconnecting", n=self.retry_n, m=5))
            host = old.cast_info.host
            try:
                old.disconnect(timeout=2)
            except Exception:
                pass
            self.devices[name] = self.direct(host)
            self.connect(name)
        except Exception:
            log(traceback.format_exc())
            self.set_online(False)
        finally:
            self.reconnecting = False

    def by_ip(self):
        self.cfg["ip"] = self.ip.get().strip()
        save_cfg(self.cfg)
        self.discover()

    def connect(self, name):
        cast = self.devices.get(name)
        if not cast:
            return
        self.set_status("st_connecting", "orange", name=name)
        self.cur_dev = name

        def work():
            try:
                cast.wait(timeout=12)
                self.chromecast = cast
                if self.target == "cast":
                    self.cast = cast
                if not getattr(cast, "_watcher", None):
                    cast._watcher = Watcher(self)
                    cast.media_controller.register_status_listener(cast._watcher)
                self.cfg["last"] = name
                save_cfg(self.cfg)
                self.cur_dev = name
                self.set_online(True)
                self.ui(self.fill_devices)
            except Exception as e:
                log(traceback.format_exc())
                if self.target == "cast":
                    self.cast = None
                self.set_online(False)
                self.msg(T("conn_fail", e=e))
        self.bg(work)

    def mc(self):
        if not self.cast:
            self.msg(T("no_tv"))
            return None
        return self.cast.media_controller

    # ---------- fila e músicas ----------
    def play_link(self, replace):
        url = self.link.get().strip()
        if not url:
            self.msg(T("paste_first"))
            return
        if self.mc():
            self.bg(lambda: self.add_url(url, replace))

    def add_url(self, url, replace):
        url = (url or "").strip()
        if not valid_media_url(url):
            self.msg(T("bad_url"))
            return
        _, deno = self.get_tools()
        self.msg(T("reading_link"))
        try:
            new, start = load_tracks(url, deno)
        except Exception as e:
            self.msg(T("bot_help") if BOT in str(e) else T("read_fail", e=str(e)[:200]))
            return
        self.add_tracks(new, replace, start)

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title=T("pick_files"),
            filetypes=[(T("ft_media"), "*.mp4 *.mkv *.avi *.mov *.webm *.wmv *.flv *.ts *.m4v "
                                          "*.mp3 *.m4a *.aac *.wav *.flac *.ogg *.opus"), (T("ft_all"), "*.*")])
        if paths and self.mc():
            new = [{"title": os.path.splitext(os.path.basename(p))[0], "path": p} for p in paths]
            self.bg(lambda: self.add_tracks(new, False))

    def add_tracks(self, new, replace=False, start=0, name=""):
        self.get_tools()
        if replace or not self.tracks:
            self.blocked_until = 0  # ação do usuário: tenta de novo agora
            self.tracks, self.orig, self.idx = list(new), None, 0
            self.queue_name = name
            self.failed.clear()
            if self.shuffle_on and len(self.tracks) > 1:
                self.orig = list(self.tracks)
                cur = self.tracks[start]
                rest = [x for x in self.tracks if x is not cur]
                random.shuffle(rest)
                self.tracks, start = [cur] + rest, 0
            self.ui(self.fill_list)
            self.msg(T("n_in_queue", n=len(new)))
            self.play_index(start)
        else:
            first = len(self.tracks)
            self.tracks += new
            if self.orig is not None:
                self.orig += new
            self.ui(self.fill_list)
            self.msg(T("n_added", n=len(new)))
            if not (self.armed or self.playing):
                self.play_index(first)

    def fill_list(self):
        self.q_lbl.config(text=T("queue_from", name=self.queue_name) if self.queue_name else "")
        self.lst.delete(0, "end")
        for n, t in enumerate(self.tracks, 1):
            self.lst.insert("end", f"{n}. {'💾 ' if t.get('path') else ''}{t['title']}")
        if self.tracks:
            self.select_row(min(self.idx, len(self.tracks) - 1))
        self.update_dl()

    def update_dl(self):
        """Conta quantos itens da fila já estão no computador. Roda em segundo plano (com muitos arquivos a conta
        pode demorar) e junta pedidos seguidos numa conta só."""
        with self._dl_lock:
            if self._dl_busy:
                self._dl_again = True
                return
            self._dl_busy, self._dl_again = True, False

        def work():
            txt = ""
            try:
                tracks = list(self.tracks)
                n = len(tracks)
                ready = sum(1 for t in tracks if (os.path.isfile(t["path"]) if t.get("path") else self.offline_info(t)))
                txt = T("dl_count", r=ready, n=n) if n else ""
            except Exception:
                log(traceback.format_exc())
            self.ui(lambda: self.dl_lbl.config(text=txt))
            with self._dl_lock:
                self._dl_busy = False
                again = self._dl_again
            if again and not self.closing:
                self.update_dl()
        threading.Thread(target=work, daemon=True).start()

    def over_limit(self):
        limit = float(CFGS["max_gb"]) * 1024 ** 3
        if limit <= 0:
            return False
        total = 0
        for t in self.tracks:
            inf = self.offline_info(t)
            if inf and os.path.isfile(inf["path"]):
                total += os.path.getsize(inf["path"])
        return total > limit

    def stop_bulk(self, why):
        self.bulk = False
        CFGS["gap"] = 4.0
        self.ui(lambda: self.bulk_btn.config(text=T("bulk_start")))
        self.msg(why)

    def toggle_bulk(self):
        if self.bulk:
            self.stop_bulk(T("bulk_stopped"))
            return
        if not self.tracks:
            self.msg(T("queue_empty_dl"))
            return
        self.bulk, CFGS["gap"] = True, 8.0
        self.bulk_btn.config(text=T("bulk_stop"))
        self.msg(T("bulk_started"))

    def select_row(self, i):
        self.lst.selection_clear(0, "end")
        self.lst.selection_set(i)
        self.lst.see(i)

    def offline_info(self, t):
        """Item pronto para tocar SEM pedir nada ao site (ou None)."""
        k = (tkey(t), mkey())
        if k in self.cache and os.path.isfile(self.cache[k]["path"]):
            return self.cache[k]
        if t.get("path"):
            if not os.path.isfile(t["path"]):
                return None
            inf = prepare_local(t["path"], self.tools[0] if self.tools else None, convert=False)
        else:
            vid = t.get("id") or video_id(t.get("url"))
            inf = _cached(vid, mkey()) if vid else None
        if inf:
            self.cache[k] = inf
        return inf

    def get_info(self, t, quiet=False):
        inf = self.offline_info(t)
        if inf:
            return inf
        k = (tkey(t), mkey())
        if t.get("path"):
            if not os.path.isfile(t["path"]):
                raise RuntimeError(T("err_notfound", p=t["path"]))
            if not quiet:
                self.msg(T("converting"))
            inf = prepare_local(t["path"], self.tools[0])
        else:
            if time.time() < self.blocked_until:
                raise Blocked()
            last = {"b": -1}

            def prog(p):
                if not quiet and p // 25 != last["b"]:
                    last["b"] = p // 25
                    self.msg(T("downloading", p=p))
            with self.fetch_lock:
                inf = self.offline_info(t)
                if not inf:
                    try:
                        inf = fetch_video(t["url"], t.get("id"), self.tools[0], self.tools[1],
                                          mkey(), prog,
                                          lambda: self.msg(T("updating_yt")))
                    except Exception as e:
                        if BOT in str(e):
                            self.blocked_until = time.time() + 900
                            if time.time() > self.block_msg_until:
                                self.block_msg_until = self.blocked_until
                                self.msg(T("bot_help"))
                            raise Blocked()
                        raise
        self.cache[k] = inf
        return inf

    def play_index(self, i, start=0):
        with self.play_lock:
            offline_only, tried, last_err = False, 0, ""
            while 0 <= i < len(self.tracks) and tried < len(self.tracks):
                tried += 1
                t = self.tracks[i]
                try:
                    self.armed = False
                    if offline_only:
                        info = self.offline_info(t)
                        if not info:
                            i += 1
                            continue
                    else:
                        self.msg(T("preparing_item", i=i + 1, n=len(self.tracks), t=t["title"]))
                        info = self.get_info(t)
                    screen = self.visual_for(info) if info["ctype"].startswith("audio") else None
                    stream = self.server.url_for(screen or info["path"], self.cast.cast_info.host)
                    mc = self.cast.media_controller
                    kw = {"title": info["title"], "current_time": start}
                    ctype = "video/mp4" if screen else info["ctype"]
                    if info.get("thumb") and not screen:
                        kw["thumb"] = info["thumb"]
                    if ctype.startswith("audio"):
                        kw["metadata"] = {"metadataType": 3, "title": info["title"],
                                          "artist": info.get("artist", "")}
                    sub = None if screen or ctype.startswith("audio") else self.subs_for(t)
                    if sub:
                        kw.update(subtitles=self.server.url_for(sub, self.cast.cast_info.host),
                                  subtitles_lang=mediatools.CAST_LANG[CFGS["subs"]], subtitles_mime="text/vtt")
                    t0 = time.time()
                    mc.play_media(stream, ctype, **kw)
                    mc.block_until_active(timeout=30)
                    if sub:
                        try:
                            mc.enable_subtitle(1)
                        except Exception:
                            log("legenda: " + traceback.format_exc())
                    self.latency = min(6.0, max(0.8, 0.6 * self.latency + 0.4 * (time.time() - t0)))
                    self.idx, self.dur, self.cur_title = i, info.get("duration") or 0, info["title"]
                    self.cur_path = info["path"]
                    self.armed = True
                    extra = ((f"  ·  {info['artist']}" if info.get("artist") else "")
                             + (f"  ·  {info['height']}p" if info.get("height") else ""))
                    self.now_state = {"title": info["title"], "i": i + 1, "n": len(self.tracks), "extra": extra}
                    self.ui(lambda i=i: (self.select_row(i), self.render_now()))
                    self.msg(T("playing_item", i=i + 1, n=len(self.tracks), t=info["title"])
                             + (f" · {info['height']}p" if info.get("height") else ""))
                    prune({info["path"], screen or ""} | {x["path"] for x in self.cache.values()}
                          | {x.get("path") or "" for x in list(self.tracks)})
                    trim_visuals(screen)
                    self.refresh_usage()
                    return
                except Blocked:
                    offline_only = True
                    i += 1
                except Exception as e:
                    log(traceback.format_exc())
                    last_err = str(e)[:200]
                    self.msg(T("play_fail", t=t["title"], e=last_err[:150]))
                    self.failed.add(tkey(t))
                    i += 1
            if offline_only:
                hora = time.strftime("%H:%M", time.localtime(self.blocked_until))
                self.msg(T("stopped_blocked", h=hora))
            else:
                self.msg(T("stopped_none", e=last_err or T("unknown")))

    def subs_for(self, t):
        """Legenda (WebVTT) do item, no idioma escolhido em Ajustes; None se desligada ou se não existir."""
        lang = CFGS.get("subs", "off")
        if lang == "off":
            return None
        try:
            if t.get("path"):
                return mediatools.local_vtt(t["path"], lang, CFGS["cache"], self.tools[0])
            if t.get("url") and time.time() >= self.blocked_until:
                return mediatools.youtube_vtt(t["url"], t.get("id") or video_id(t["url"]), lang, CFGS["cache"],
                                              common(self.tools[1]))
        except Exception:
            log("legendas:\n" + traceback.format_exc())
        return None

    def visual_file(self, info):
        """Caminho da tela (Capa) desta faixa, ou None se estiver desligada ou não der para usar."""
        if visuals is None or not self.tools or not info.get("path"):
            return None
        style = CFGS.get("screen", "cover")
        if style != "cover":
            return None
        key = visuals.key_for(info["path"], style)
        return os.path.join(CFGS["cache"], "visuals", key + ".mp4"), style

    def visual_for(self, info, quiet=False):
        """Gera (uma vez só) o vídeo da tela com a música. Se algo falhar, devolve None e o áudio toca normalmente."""
        try:
            r = self.visual_file(info)
            if not r:
                return None
            out, style = r
            if os.path.isfile(out):
                os.utime(out)
                return out
            if out in self.vis_failed:
                return None
            with self.vis_lock:
                if os.path.isfile(out):
                    return out
                title, artist = info.get("title") or "", info.get("artist") or ""
                if info.get("local"):
                    t2, a2 = visuals.tags_of(info["path"])
                    title, artist = t2 or title, a2 or artist
                last = {"b": -1}
                name = T("s_cover")

                def prog(p):
                    if not quiet and p // 20 != last["b"]:
                        last["b"] = p // 20
                        self.msg(T("vis_making", s=name, p=p))
                if not quiet:
                    self.msg(T("vis_making", s=name, p=0))
                dur = info.get("duration") or 0
                ok = visuals.build(self.tools[0], info["path"], out, style, title, artist, APP_NAME, T("vis_kicker"),
                                   art_url=info.get("thumb"), progress=prog, cancelled=lambda: self.closing,
                                   timeout=max(240, dur * 3))
                if not ok:
                    self.vis_failed.add(out)
                    log("visuals: " + visuals.LAST_ERR[0])
                return out if ok else None
        except Exception:
            log(traceback.format_exc())
            return None

    def next_index(self):
        if self.idx + 1 < len(self.tracks):
            return self.idx + 1
        return 0 if (self.repeat_on and self.tracks) else None

    def advance(self):
        if self.stop_after:
            self.stop_after = False
            self.ui(lambda: self.sleep_cb.set(T("sleep_off")))
            self.msg(T("timer_end_done"))
            m = self.cast and self.cast.media_controller
            m and m.stop()
            return
        nxt = self.next_index()
        if nxt is None:
            self.msg(T("end_of_list"))
        else:
            self.bg(lambda: self.play_index(nxt))

    def on_finished(self):
        if self.armed:
            self.armed = False
            self.advance()

    def try_early(self):
        """Troca um pouco antes do fim, para quase não haver pausa entre os itens."""
        nxt = self.next_index()
        if nxt is None or self.stop_after or not self.offline_info(self.tracks[nxt]):
            return
        self.armed = False
        self.bg(lambda: self.play_index(nxt))

    def next_track(self):
        if self.mc() and self.tracks:
            nxt = self.next_index()
            if nxt is None:
                self.msg(T("last_item"))
            else:
                self.bg(lambda: self.play_index(nxt))

    def prev_track(self):
        m = self.mc()
        if m and self.tracks:
            if self.pos > 5:
                self.bg(lambda: m.seek(0))
            else:
                self.bg(lambda: self.play_index(max(0, self.idx - 1)))

    def pick(self):
        sel = self.lst.curselection()
        if sel and self.mc():
            self.blocked_until = 0
            self.bg(lambda: self.play_index(sel[0]))

    def pause(self):
        m = self.mc()
        m and self.bg(m.pause)

    def resume(self):
        m = self.mc()
        m and self.bg(m.play)

    def stop(self):
        self.armed = False
        m = self.mc()
        m and self.bg(m.stop)

    # ---------- linha do tempo e volume ----------
    @staticmethod
    def fmt(t):
        t = int(max(0, t))
        h, r = divmod(t, 3600)
        m, s = divmod(r, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    def on_tl(self, v):
        if not self.updating:
            self.t_now.config(text=self.fmt(float(v)))

    def set_timeline(self, pos, dur):
        if self.dragging:
            return
        self.updating = True
        if dur:
            self.tl.config(to=dur)
            self.t_total.config(text=self.fmt(dur))
        self.tl.set(pos)
        self.t_now.config(text=self.fmt(pos))
        self.updating = False

    def tl_release(self, v):
        self.dragging = False
        self.seek(float(v))

    def seek(self, t):
        m = self.mc()
        if m:
            self.pos = t
            self.bg(lambda: m.seek(t))

    def on_vol_move(self, v):
        self.vol_lbl.config(text=f"{int(v)}%")
        if time.time() - self._vol_t > 0.15:
            self._vol_t = time.time()
            self.send_vol(v)

    def on_vol_release(self, v):
        self.vol_drag = False
        self.vol_lbl.config(text=f"{int(v)}%")
        self.send_vol(v)

    def send_vol(self, v):
        if self.cast:
            try:
                self.cast.set_volume(float(v) / 100)
            except Exception:
                pass

    def skip(self, delta):
        m = self.mc()
        if not m:
            return
        try:
            cur = m.status.adjusted_current_time if m.status else self.pos
        except Exception:
            cur = self.pos
        top = (self.dur_now or self.dur or 10 ** 6) - 1
        self.seek(max(0.0, min(top, (cur or 0) + delta)))

    def set_quality(self, q):
        CFGS["quality"] = q
        self.cfg["quality"] = q
        save_cfg(self.cfg)
        if CFGS["mode"] == "audio":
            self.msg(T("audio_q"))
            return
        names = {v: k for k, v in self.quals()}
        self.msg(T("q_set", q=names.get(q, q))
                 + (T("q_restart") if (self.cast and self.tracks and self.armed) else "."))
        if q in ("1440", "2160"):
            self.msg(T("q_4k"))
        if self.cast and self.tracks and self.armed:
            pos = int(self.pos)
            self.bg(lambda: self.play_index(self.idx, start=pos))

    def _focus_class(self):
        try:
            w = self.focus_get()
            return w.winfo_class() if w else ""
        except Exception:  # ex.: lista aberta de um combobox
            return ""

    def key_ok(self):
        """Teclas de comando só valem quando a pessoa NÃO está digitando num campo."""
        return self._focus_class() not in ("TEntry", "Entry", "TCombobox", "TSpinbox", "Text", "Spinbox")

    def _keys(self):
        """Atalhos do programa inteiro (as janelas de pergunta têm os próprios)."""
        b = self.bind

        def do(fn, lists=True, arrows=False):
            """Cria o comando de tecla: ignora quando digitando; 'lists=False' deixa a lista usar a tecla."""
            def h(e):
                cls = self._focus_class()
                if not self.key_ok():
                    return None
                if not lists and cls == "Listbox":
                    return None
                if arrows and cls in ("TScale", "Scale", "TScrollbar"):
                    return None
                fn()
                return "break"
            return h

        def space(e):
            cls = self._focus_class()
            if not self.key_ok() or cls in ("TCheckbutton", "TRadiobutton", "Canvas", "TButton"):
                return None  # esses já usam a barra de espaço para ativar o próprio botão
            if cls == "Listbox" and getattr(e, "widget", None) in (getattr(self, "files_list", None),
                                                                    getattr(self, "pl_list", None),
                                                                    getattr(self, "pl_items", None)):
                return None  # nas listas de arquivos/playlists a barra marca o item
            self.toggle_play()
            return "break"
        b("<space>", space)
        b("<Left>", do(lambda: self.skip(-10), arrows=True))
        b("<Right>", do(lambda: self.skip(10), arrows=True))
        b("<Shift-Left>", do(lambda: self.skip(-30), arrows=True))
        b("<Shift-Right>", do(lambda: self.skip(30), arrows=True))
        b("<Up>", do(lambda: self.change_vol(5), lists=False, arrows=True))
        b("<Down>", do(lambda: self.change_vol(-5), lists=False, arrows=True))
        b("<Control-Right>", do(self.next_track))
        b("<Control-Left>", do(self.prev_track))
        b("<Key-n>", do(self.next_track, lists=False))
        b("<Key-p>", do(self.prev_track, lists=False))
        b("<Key-m>", do(self.toggle_mute, lists=False))
        b("<Key-s>", do(self.stop, lists=False))
        for n, key in enumerate(("play", "lists", "files", "set"), 1):
            for mod in ("Control", "Alt"):
                b(f"<{mod}-Key-{n}>", lambda e, k=key: (self.show_page(k), "break")[-1])
        b("<Control-Tab>", lambda e: (self.cycle_page(1), "break")[-1])
        b("<Control-Shift-Tab>", lambda e: (self.cycle_page(-1), "break")[-1])
        b("<Control-ISO_Left_Tab>", lambda e: (self.cycle_page(-1), "break")[-1])
        b("<Control-Key-l>", lambda e: (self.focus_link(), "break")[-1])
        b("<F6>", lambda e: (self.focus_link(), "break")[-1])
        b("<Control-Key-f>", lambda e: (self.focus_search(), "break")[-1])
        b("<Control-Key-o>", lambda e: (self.add_files(), "break")[-1])
        b("<Control-Key-s>", lambda e: (self.save_playlist(), "break")[-1])
        b("<Control-Key-n>", lambda e: (self.new_playlist(), "break")[-1])
        b("<Control-Key-q>", lambda e: (self.on_close(), "break")[-1])
        b("<F1>", lambda e: (self.show_keys(), "break")[-1])
        b("<F5>", lambda e: (self.refresh_files() if self.cur_page == "files" else self.discover(), "break")[-1])
        b("<F11>", lambda e: (self.frame.toggle_max() if self.frame else None, "break")[-1])

    def cycle_page(self, d):
        keys = list(self.tab_btns)
        self.show_page(keys[(keys.index(self.cur_page) + d) % len(keys)])

    def focus_link(self):
        self.show_page("play")
        self.link.focus_set()
        self.link.select_range(0, "end")

    def focus_search(self):
        self.show_page("files")
        self.files_q.focus_set()
        self.files_q.select_range(0, "end")

    def change_vol(self, delta):
        v = max(0, min(100, float(self.vol_val) + delta))
        self.vol_val = v
        self.vol.set(v)
        self.vol_lbl.config(text=f"{int(v)}%")
        self.send_vol(v)

    def toggle_mute(self):
        if self.vol_val > 0:
            self._mute_prev, v = self.vol_val, 0
        else:
            v = getattr(self, "_mute_prev", 50) or 50
        self.vol_val = v
        self.vol.set(v)
        self.vol_lbl.config(text=f"{int(v)}%")
        self.send_vol(v)

    def remove_queue_item(self):
        sel = self.lst.curselection()
        if not sel or sel[0] >= len(self.tracks):
            return
        i = sel[0]
        if i == self.idx and (self.armed or self.playing):
            self.msg(T("q_rm_playing"))
            return
        t = self.tracks.pop(i)
        if self.orig is not None and t in self.orig:
            self.orig.remove(t)
        if i < self.idx:
            self.idx -= 1
        self.fill_list()
        if self.tracks:
            j = min(i, len(self.tracks) - 1)
            self.lst.selection_set(j)
            self.lst.activate(j)

    def show_keys(self):
        dialogs.show_keys(self)

    def show_welcome(self):
        """Mostra de novo a tela de boas-vindas (só para ler; não muda nada)."""
        self.wait_window(TermsGate(self))

    EXPORT_KEYS = ("playlists", "lang", "theme", "size", "mode", "quality", "max_gb", "subs", "norm", "hevc",
                   "lookahead", "adjust", "target", "fold")

    def export_cfg(self):
        path = filedialog.asksaveasfilename(title=T("bk_export"), defaultextension=".json",
                                            initialfile="livingplay-backup.json",
                                            filetypes=[("JSON", "*.json")])
        if not path:
            return
        data = {"livingplay_backup": 1, **{k: self.cfg[k] for k in self.EXPORT_KEYS if k in self.cfg}}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            self.msg(T("bk_saved", n=len(data.get("playlists", {}))))
        except OSError as e:
            self.msg(T("bk_err", e=str(e)[:120]))

    def import_cfg(self):
        path = filedialog.askopenfilename(title=T("bk_import"), filetypes=[("JSON", "*.json"), (T("ft_all"), "*.*")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "livingplay_backup" not in data:
                raise ValueError(T("bk_not"))
            pls = data.get("playlists") or {}
            if not isinstance(pls, dict) or not all(isinstance(v, list) for v in pls.values()):
                raise ValueError(T("bk_not"))
        except Exception as e:
            self.msg(T("bk_err", e=str(e)[:120]))
            return
        if not dialogs.confirm(self, T("bk_import"), T("bk_ask", n=len(pls), nl="\n\n"), default_no=True):
            return
        data = sanitize_cfg(data)  # descarta qualquer valor estranho do arquivo
        pls = data.get("playlists") or {}
        for k in self.EXPORT_KEYS:
            if k in data and k != "playlists":
                self.cfg[k] = data[k]
        self.cfg.setdefault("playlists", {}).update(pls)
        self._save_pls()
        self.msg(T("bk_done", n=len(pls)))

    def toggle_play(self):
        m = self.mc()
        if not m:
            return
        if self.playing:
            self.bg(m.pause)
        elif m.status and m.status.player_state == "PAUSED":
            self.bg(m.play)
        elif self.tracks:
            self.bg(lambda: self.play_index(min(self.idx, len(self.tracks) - 1)))
        else:
            self.msg(T("paste_start"))

    def render_now(self):
        st = self.now_state
        if not st:
            self.now_title.config(text=T("nothing"))
            self.now_sub.config(text=T("now_hint"))
            return
        self.now_title.config(text=st["title"])
        self.now_sub.config(text=T("now_item", i=st["i"], n=st["n"]) + st["extra"])

    def refresh_toggles(self):
        self.btn_shuf.config(style="ToggleOn.TButton" if self.shuffle_on else "Toggle.TButton")
        self.btn_rep.config(style="ToggleOn.TButton" if self.repeat_on else "Toggle.TButton")

    # ---------- aleatório, timer ----------
    def set_shuffle(self, on):
        if on == self.shuffle_on:
            return
        self.shuffle_on = on
        self.ui(lambda: (self.v_shuf.set(on), self.refresh_toggles()))
        if not self.tracks:
            return
        cur = self.tracks[self.idx] if self.idx < len(self.tracks) else None
        if on:
            self.orig = list(self.tracks)
            rest = [x for x in self.tracks if x is not cur]
            random.shuffle(rest)
            self.tracks, self.idx = ([cur] if cur else []) + rest, 0
        elif self.orig:
            self.tracks, self.orig = self.orig, None
            self.idx = next((i for i, x in enumerate(self.tracks) if x is cur), 0)
        self.ui(self.fill_list)

    def set_repeat(self, on):
        self.repeat_on = on
        self.ui(lambda: (self.v_rep.set(on), self.refresh_toggles()))

    def set_sleep(self, v):
        self.sleep_at, self.stop_after = None, False
        names = {val: k for k, val in self.sleeps()}
        self.ui(lambda: self.sleep_cb.set(names.get(str(v), T("sleep_off"))))
        if v == "end":
            self.stop_after = True
            self.msg(T("timer_end_set"))
        elif str(v) not in ("0", ""):
            self.sleep_at = time.time() + int(v) * 60
            self.msg(T("timer_n_set", n=v))

    # ---------- ajustes ----------
    def toggle_frame(self):
        self.cfg["native_frame"] = bool(self.var_native.get())
        with self.cfg_lock:
            save_cfg(self.cfg)
        self.msg(T("frame_restart"))

    def toggle_cookies(self):
        """cookies.txt é opcional e começa desligado: ligar exige confirmação explícita."""
        if self.var_ck.get():
            if not dialogs.confirm(self, T("ck_title"), T("ck_warn"), default_no=True):
                self.var_ck.set(False)
                return
        CFGS["cookies_file"] = bool(self.var_ck.get())
        self.apply_settings()

    def ask_terms(self):
        """Aviso da primeira execução: resumo dos termos e confirmação do usuário."""
        if self.closing:
            return
        gate = TermsGate(self)
        self.wait_window(gate)
        if gate.accepted:
            self.cfg["terms_ok"] = TERMS_VERSION
            save_cfg(self.cfg)
        else:
            self.on_close()

    def apply_settings(self, _e=None):
        try:
            CFGS["max_gb"] = max(0.0, float(self.var_max.get().replace(",", ".")))
            self.lookahead = max(1, min(20, int(float(self.var_look.get()))))
            self.adjust = float(self.var_adj.get().replace(",", "."))
        except ValueError:
            pass
        if self.var_mode.get() != CFGS["mode"]:
            CFGS["mode"] = self.var_mode.get()
            self.msg(T("mode_set_audio") if CFGS["mode"] == "audio" else T("mode_set_video"))
        CFGS["screen"] = "cover"  # a Aurora foi removida: sobrou só a Capa (configurações antigas com "aurora" viram Capa)
        self.cfg["screen"] = "cover"
        if self.var_subs.get() in ("off", "pt", "en"):
            CFGS["subs"] = self.var_subs.get()
        CFGS["norm"], CFGS["hevc"] = bool(self.var_norm.get()), bool(self.var_hevc.get())
        self.cfg.update(subs=CFGS["subs"], norm=CFGS["norm"], hevc=CFGS["hevc"])
        self.cfg.pop("browser", None)  # versões antigas guardavam o navegador dos cookies; não é mais usado
        self.cfg.update(max_gb=CFGS["max_gb"], lookahead=self.lookahead, adjust=self.adjust,
                        mode=CFGS["mode"], cookies_file=bool(CFGS.get("cookies_file")), cache=CFGS["cache"])
        again = False
        th = next((k for k in PALETTES if T("th_" + k) == self.var_theme.get()), self.theme)
        self.cfg["theme"] = th
        if th != self.theme:
            self.theme, self.pal = th, PALETTES[th]
            again = True
        sz = next((k for k in SIZES if T("sz_" + k) == self.var_size.get()), self.size_name)
        if sz != self.size_name:
            self.size_name = sz
            self.uf, self.fs = SIZES[sz]
            self.u = self.k * self.uf
            self.cfg["size"] = sz
            again = True
        with self.cfg_lock:
            save_cfg(self.cfg)
        if again:
            self.after(60, self.rebuild)

    def change_lang(self, _e=None):
        self.apply_language(next((k for k, v in LANGS.items() if v == self.var_lang.get()), LANG["v"]))

    def apply_language(self, code):
        if code == LANG["v"]:
            return
        set_lang(code)
        with self.cfg_lock:
            self.cfg["lang"] = code
            save_cfg(self.cfg)
        self.msg(T("lang_saved"))
        self.after(60, self.rebuild)

    def on_target(self, value):
        if value == self.target:
            return
        if self.switching:
            self.msg(T("sw_busy"))
            self.target_sw.set(self.target)
            return
        if value == "cast" and not (self.chromecast and self.chromecast.socket_client.is_connected):
            self.msg(T("sw_nocast"))
            self.target_sw.set(self.target)
            return
        self.switching = True
        self.bg(lambda: self.switch_to(value))

    def switch_to(self, value):
        """Troca o destino do som e da imagem, continuando do mesmo ponto. Nunca toca nos dois ao mesmo tempo."""
        old, old_target = self.cast, self.target
        idx, had = self.idx, bool(self.tracks and (self.armed or self.playing))
        was_playing = self.playing
        try:
            pos = self.pos
            try:
                st = old.media_controller.status if old else None
                if st and st.player_state in ("PLAYING", "PAUSED", "BUFFERING"):
                    pos = st.adjusted_current_time or pos
            except Exception:
                pass
            self.armed = False
            if old:
                try:
                    old.media_controller.stop()
                except Exception:
                    pass
            new = self.get_pcdev() if value == "pc" else self.chromecast
            with self.cfg_lock:
                self.cfg["target"] = value
                save_cfg(self.cfg)
            self.target, self.cast, self.playing, self._shown_playing = value, new, False, None
            if value == "pc":
                self.set_status("st_pc", "green")
            else:
                self.set_online(True)
            if had:
                self.play_index(idx, start=int(pos))
                if not self.armed:
                    raise RuntimeError("falhou ao retomar")
                if not was_playing:
                    new.media_controller.pause()
            self.msg(T("sw_to_pc" if value == "pc" else "sw_to_cast"))
        except Exception:
            log(traceback.format_exc())
            self.target, self.cast = old_target, old
            with self.cfg_lock:
                self.cfg["target"] = old_target
                save_cfg(self.cfg)
            if old_target == "pc":
                self.set_status("st_pc", "green")
            else:
                self.set_online(bool(old))
            self.msg(T("sw_failed"))
            if had and old:
                try:
                    self.play_index(idx, start=int(pos))
                except Exception:
                    log(traceback.format_exc())
        finally:
            self.switching = False
            self.ui(lambda: self.target_sw.set(self.target))

    def open_tutorial(self):
        t = getattr(self, "tut", None)
        try:
            if t and t.winfo_exists():
                t.lift()
                t.focus_set()
                return
        except Exception:
            pass
        self.tut = Tutorial(self)

    SPACE_LEVELS = (50, 75, 90, 100)

    def space_numbers(self, inv):
        used = sum(x[1] for x in inv["videos"])
        limit = float(CFGS["max_gb"]) * 1024 ** 3
        return used, limit, (int(used * 100 / limit) if limit > 0 else None)

    def refresh_usage(self):
        """Recalcula (em segundo plano) quanto espaço os vídeos ocupam e avisa quando a pasta enche (50, 75, 90, 100%)."""
        def work():
            if unsafe_dir(CFGS["cache"]):
                txt, nums = T("usage_unsafe"), None
            else:
                inv = cache_inventory()
                v = [x for x in inv["videos"] if not x[0].endswith(".json")]
                nums = self.space_numbers(inv)
                txt = T("usage_fmt", v=fmt_size(nums[0]), nv=len(v),
                        c=fmt_size(sum(x[1] for x in inv["temp"])), nc=len(inv["temp"]))
                txt += "\n" + (T("usage_pct", p=nums[2], l=fmt_size(nums[1])) if nums[2] is not None
                               else T("usage_nolimit"))
            self.ui(lambda: self.space_ui(txt, nums))
        threading.Thread(target=work, daemon=True).start()

    def space_ui(self, txt, nums):
        try:
            self.usage_lbl.config(text=txt)
            self.space_nums = nums
            self.draw_space_bar()
            pct = nums[2] if nums else None
            level = max([lv for lv in self.SPACE_LEVELS if pct is not None and pct >= lv] or [0])
            if pct is not None and pct >= 50:
                self.space_btn.config(text=T("space_btn", p=pct))
                self.space_flow.show(self.space_btn, True)
            else:
                self.space_flow.show(self.space_btn, False)
            if level > self.space_level:
                key = "space_full" if level >= 100 else "space_90" if level >= 90 else "space_warn"
                self.msg(T(key, p=pct, u=fmt_size(nums[0]), l=fmt_size(nums[1])))
            self.space_level = level
        except tk.TclError:
            pass

    def draw_space_bar(self):
        c = getattr(self, "space_bar", None)
        nums = getattr(self, "space_nums", None)
        if not c or not c.winfo_exists():
            return
        w, h = c.winfo_width(), c.winfo_height()
        if w < 20:
            return
        p = self.pal
        c.delete("all")
        rrect(c, 0, 1, w, h - 1, (h - 2) / 2, fill=p["border"], outline="")
        if nums and nums[2] is not None and nums[2] > 0:
            col = p["bad"] if nums[2] >= 90 else p["warn"] if nums[2] >= 75 else p["accent"]
            fw = max(h, int(w * min(nums[2], 100) / 100))
            rrect(c, 0, 1, fw, h - 1, (h - 2) / 2, fill=col, outline="")

    def goto_storage(self):
        self.show_page("set")
        try:
            self.folds["s_store"][2](True, False)
        except Exception:
            pass

    def clean_cache(self):
        inv = cache_inventory()["temp"]
        if not inv:
            self.msg(T("clean_none"))
            self.refresh_usage()
            return
        if not dialogs.confirm(self, T("clean_title"), T("clean_ask", n=len(inv), s=fmt_size(sum(x[1] for x in inv)),
                                                         nl="\n\n")):
            return
        n, size, _, errs = delete_files(inv, keep=[self.cur_path])
        self.after_cleanup(T("clean_done", n=n, s=fmt_size(size)), errs)

    def delete_videos(self):
        inv = cache_inventory()["videos"]
        vids = [x for x in inv if not x[0].endswith(".json")]
        if not vids:
            self.msg(T("delv_none"))
            self.refresh_usage()
            return
        if not dialogs.confirm(self, T("delv_title"), T("delv_ask", n=len(vids), s=fmt_size(sum(x[1] for x in inv)),
                                                        nl="\n\n"), default_no=True):
            return
        inv = cache_inventory()["videos"]  # relê: pode ter mudado enquanto o aviso estava aberto
        keep = [self.cur_path] if (self.armed or self.playing) else []
        n, size, kept, errs = delete_files(inv, keep=keep)
        if kept:  # o vídeo em uso ficou: mantém o arquivo de controle dele também
            pass
        self.after_cleanup(T("delv_done", n=len([1 for x in vids if not os.path.exists(x[0])]), s=fmt_size(size))
                           + (T("delv_inuse", k=kept) if kept else ""), errs)

    def after_cleanup(self, text, errs):
        self.cache.clear()
        self.failed.clear()
        self.msg(text)
        if errs:
            self.msg(T("clean_fail", n=len(errs), e=errs[0][:120]))
        self.refresh_usage()
        self.update_dl()

    def choose_dir(self):
        d = filedialog.askdirectory(initialdir=CFGS["cache"], title=T("choose_dir_t"))
        if d and unsafe_dir(d):  # raiz do disco, pasta do usuário, Windows...: espalharia arquivos onde não deve
            self.msg(T("dir_unsafe"))
            return
        if d:
            try:
                os.makedirs(d, exist_ok=True)
            except OSError as e:
                self.msg(T("dir_fail", e=e))
                return
            CFGS["cache"] = d
            self.var_dir.set(d)
            self.apply_settings()
            self.refresh_usage()
            self.msg(T("dir_set", d=d))

    def open_dir(self):
        d = CFGS["cache"]
        try:
            os.makedirs(d, exist_ok=True)
            if not os.path.isdir(d):  # só abre pasta; nunca executa um arquivo
                raise OSError(d)
            if sys.platform.startswith("win"):
                os.startfile(d)  # noqa
            else:
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", d],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            self.msg(T("open_fail", e=e))

    # ---------- sessão e playlists ----------
    @staticmethod
    def compact(tracks):
        return [{k: t[k] for k in ("id", "title", "url", "path") if t.get(k)} for t in tracks[:300]]

    def save_session(self):
        if not self.tracks:
            return
        with self.cfg_lock:
            self.cfg["session"] = {"tracks": self.compact(self.tracks), "idx": self.idx,
                                   "pos": int(self.pos), "name": self.queue_name}
            save_cfg(self.cfg)

    def resume_session(self):
        s = self.cfg.get("session")
        if not s or not s.get("tracks"):
            self.msg(T("no_session"))
            return
        if not self.mc():
            return
        self.get_tools()
        self.tracks, self.orig, self.queue_name = list(s["tracks"]), None, s.get("name", "")
        self.idx = min(int(s.get("idx", 0)), len(self.tracks) - 1)
        self.ui(self.fill_list)
        self.play_index(self.idx, start=int(s.get("pos", 0)))

    def refresh_lists(self):
        s = self.cfg.get("session")
        if s and s.get("tracks"):
            t = s["tracks"][min(s.get("idx", 0), len(s["tracks"]) - 1)]
            self.resume_lbl.config(text=T("last_session", t=t["title"], p=self.fmt(s.get("pos", 0)),
                                          n=len(s["tracks"])))
            self.resume_btn.state(["!disabled"])
        else:
            self.resume_lbl.config(text=T("no_session_lbl"))
            self.resume_btn.state(["disabled"])
        pls = self.cfg.get("playlists", {})
        names = self.pl_names()
        keep = self.sel_pl if self.sel_pl in pls else None
        self.pl_list.delete(0, "end")
        for n in names:
            self.pl_list.insert("end", T("pl_count", name=n, n=len(pls[n])))
        if keep:
            i = names.index(keep)
            self.pl_list.selection_set(i)
            self.pl_list.see(i)
        self.sel_pl = keep
        self.pl_quick.config(values=names)
        self.pl_quick.set(keep or "")
        self.show_pl_items()

    def pl_names(self):
        return sorted(self.cfg.get("playlists", {}))

    def selected_pl(self):
        sel = self.pl_list.curselection()
        if sel:
            self.sel_pl = self.pl_names()[sel[0]]
        return self.sel_pl

    def pl_selected(self):
        self.selected_pl()
        self.pl_quick.set(self.sel_pl or "")
        self.show_pl_items()

    def show_pl_items(self):
        self.pl_items.delete(0, "end")
        name = self.sel_pl
        items = self.cfg.get("playlists", {}).get(name or "")
        if items is None:
            self.pl_items_lbl.config(text=T("pl_none_sel"))
            return
        self.pl_items_lbl.config(text=T("pl_items_in", name=name))
        for n, t in enumerate(items, 1):
            self.pl_items.insert("end", f"{n}. {'💾 ' if t.get('path') else ''}{t['title']}")

    def _save_pls(self):
        with self.cfg_lock:
            save_cfg(self.cfg)
        self.refresh_lists()

    def ask_name(self, title, initial=""):
        return dialogs.ask_text(self, title, T("pl_name_q"), initial)

    def new_playlist(self):
        name = self.ask_name(T("pl_new_title"))
        if not name:
            return
        if name in self.cfg.get("playlists", {}):
            self.msg(T("pl_exists"))
            return
        self.cfg.setdefault("playlists", {})[name] = []
        self.sel_pl = name
        self._save_pls()
        self.msg(T("pl_created", name=name))

    def save_queue(self):
        """Botão da tela principal: salva a fila como playlist e já mostra a aba Playlists com ela selecionada."""
        if self.save_playlist():
            self.show_page("lists")
            try:
                names = self.pl_names()
                if self.sel_pl in names:
                    i = names.index(self.sel_pl)
                    self.pl_list.selection_clear(0, "end")
                    self.pl_list.selection_set(i)
                    self.pl_list.see(i)
                    self.pl_selected()
            except Exception:
                log(traceback.format_exc())

    def save_playlist(self):
        if not self.tracks:
            self.msg(T("pl_empty_queue"))
            return False
        name = self.ask_name(T("pl_save_title"), self.queue_name)
        if not name:
            return False
        if name in self.cfg.get("playlists", {}) and not dialogs.confirm(
                self, T("pl_save_title"), T("pl_overwrite", name=name), default_no=True):
            return False
        items = self.compact(self.orig or self.tracks)
        self.cfg.setdefault("playlists", {})[name] = items
        self.sel_pl, self.queue_name = name, name
        self._save_pls()
        self.q_lbl.config(text=T("queue_from", name=name))
        self.msg(T("pl_saved", name=name, n=len(items)))
        return True

    def rename_playlist(self):
        old = self.selected_pl()
        if not old:
            self.msg(T("pl_sel_first"))
            return
        name = self.ask_name(T("pl_rename_title"), old)
        if not name or name == old:
            return
        pls = self.cfg["playlists"]
        if name in pls:
            self.msg(T("pl_exists"))
            return
        pls[name] = pls.pop(old)
        self.sel_pl = name
        if self.queue_name == old:
            self.queue_name = name
            self.q_lbl.config(text=T("queue_from", name=name))
        self._save_pls()
        self.msg(T("pl_renamed", name=name))

    def delete_playlist(self):
        name = self.selected_pl()
        if not name:
            self.msg(T("pl_sel_first"))
            return
        if dialogs.confirm(self, T("title_delete"), T("pl_confirm_del", name=name), default_no=True):
            self.cfg["playlists"].pop(name, None)
            self.sel_pl = None
            self._save_pls()
            self.msg(T("pl_deleted", name=name))

    def open_playlist(self, name=None):
        """Toca a playlist (troca a fila atual)."""
        name = name or self.selected_pl()
        pl = self.cfg.get("playlists", {}).get(name or "")
        if pl is None:
            self.msg(T("pl_choose"))
        elif not pl:
            self.msg(T("pl_empty_pl"))
        elif self.mc():
            self.bg(lambda: self.add_tracks(list(pl), True, name=name))

    def open_quick_pl(self):
        self.open_playlist(self.pl_quick.get() or None)

    def enqueue_playlist(self):
        name = self.selected_pl()
        pl = self.cfg.get("playlists", {}).get(name or "")
        if pl is None:
            self.msg(T("pl_choose"))
        elif not pl:
            self.msg(T("pl_empty_pl"))
        elif self.mc():
            self.bg(lambda: self.add_tracks(list(pl), False))
            self.msg(T("pl_queued", n=len(pl), name=name))

    def add_link_to_playlist(self):
        name, url = self.selected_pl(), self.pl_link.get().strip()
        if not name:
            self.msg(T("pl_sel_first"))
            return
        if not url:
            self.msg(T("paste_first"))
            return

        def work():
            _, deno = self.get_tools()
            self.msg(T("reading_link"))
            try:
                new, _start = load_tracks(url, deno)
            except Exception as e:
                self.msg(T("bot_help") if BOT in str(e) else T("read_fail", e=str(e)[:200]))
                return
            items = self.cfg["playlists"].setdefault(name, [])
            have = {tkey(t) for t in items}
            add = [t for t in self.compact(new) if tkey(t) not in have]
            items.extend(add)
            self.ui(lambda: (self.pl_link.delete(0, "end"), self._save_pls()))
            self.msg(T("pl_added", n=len(add), name=name))
        self.bg(work)

    def remove_pl_item(self):
        name, sel = self.selected_pl(), self.pl_items.curselection()
        items = self.cfg.get("playlists", {}).get(name or "")
        if items is None:
            self.msg(T("pl_sel_first"))
        elif sel:
            del items[sel[0]]
            self._save_pls()
            self.msg(T("pl_item_removed"))

    # ---------- celular ----------
    def qr_window(self):
        if not self.remote:
            self.msg(T("remote_starting"))
            return
        host = self.chromecast.cast_info.host if self.chromecast else "8.8.8.8"
        url = f"http://{lan_ip(host)}:{self.remote.port}/?k={self.token}"
        w = tk.Toplevel(self, bg=self.pal["bg"])
        w.title(T("qr_title"))
        fl = winframe.begin(w, self, T("qr_title"))
        ttk.Label(w, text=T("qr_head"), font=self.f_big).pack(padx=24, pady=(18, 2))
        ttk.Label(w, text=T("qr_sub"),
                  style="Muted.TLabel").pack(padx=24, pady=(0, 10))
        try:
            import segno
            m = segno.make(url, error="m").matrix
            sz, mg = 6, 3
            n = (len(m) + 2 * mg) * sz
            cv = tk.Canvas(w, width=n, height=n, bg="white", highlightthickness=0)
            cv.pack(padx=24)
            for y, row in enumerate(m):
                for x, v in enumerate(row):
                    if v:
                        cv.create_rectangle((x + mg) * sz, (y + mg) * sz, (x + mg + 1) * sz,
                                            (y + mg + 1) * sz, fill="black", width=0)
        except Exception:
            ttk.Label(w, text=T("qr_na")).pack()
        e = ttk.Entry(w, width=46)
        e.insert(0, url)
        e.config(state="readonly")
        e.pack(padx=24, pady=12)
        ttk.Label(w, text=T("qr_fw"), style="Muted.TLabel").pack(pady=(0, 8))
        Btn(w, text=T("qr_new"), command=lambda: self.new_token(w)).pack(pady=(0, 6))
        ttk.Label(w, text=T("qr_new_h"), style="Muted.TLabel", wraplength=self.px(380),
                  justify="center").pack(padx=24, pady=(0, 18))
        winframe.show(w, self, fl)

    def new_token(self, win=None):
        """Troca o código de acesso: links e QR codes antigos param de funcionar na hora."""
        if not dialogs.confirm(self, T("qr_new"), T("qr_new_ask"), default_no=True):
            return
        self.token = secrets.token_urlsafe(18)
        self.cfg["token"] = self.token
        with self.cfg_lock:
            save_cfg(self.cfg)
        if self.pcdev:
            self.pcdev.close_window()  # a janela do PC reabre sozinha já com o código novo
        self.msg(T("qr_new_done"))
        if win is not None:
            try:
                win.destroy()
            except Exception:
                pass
            self.after(150, self.qr_window)

    def remote_state(self):
        vol = 50
        try:
            vol = int((self.cast.status.volume_level or 0) * 100)
        except Exception:
            pass
        pc = self.target == "pc"
        return {"title": self.cur_title, "idx": self.idx, "tracks": [t["title"] for t in self.tracks],
                "pos": self.pos, "dur": self.dur_now or self.dur, "playing": self.playing, "vol": vol,
                "shuffle": self.shuffle_on, "repeat": self.repeat_on, "playlists": self.pl_names(),
                "msg": self.last_msg, "target": self.target,
                "device": T("tgt_pc") if pc else (self.cur_dev or T("tgt_cast")),
                "online": True if pc else bool(getattr(self, "tv_online", False))}

    def remote_cmd(self, name, arg):
        m = self.cast.media_controller if self.cast else None
        if name == "playpause":
            self.bg(m.pause if self.playing else m.play) if m else None
        elif name == "next":
            self.next_track()
        elif name == "prev":
            self.prev_track()
        elif name == "stop":
            self.stop()
        elif name == "skip":
            self.skip(float(arg))
        elif name == "seek" and m:
            self.seek(max(0.0, float(arg)))
        elif name == "vol" and self.cast:
            self.cast.set_volume(max(0.0, min(100.0, float(arg))) / 100)
        elif name == "target" and arg in ("cast", "pc"):
            self.ui(lambda: self.on_target(arg))
        elif name == "play_idx" and m:
            self.bg(lambda: self.play_index(int(arg)))
        elif name in ("add", "playnow") and arg and m:
            if valid_media_url(str(arg).strip()):
                self.bg(lambda: self.add_url(str(arg).strip(), name == "playnow"))
            else:
                self.msg(T("bad_url"))
        elif name == "shuffle":
            self.set_shuffle(not self.shuffle_on)
        elif name == "repeat":
            self.set_repeat(not self.repeat_on)
        elif name == "sleep":
            self.set_sleep(arg)
        elif name == "openpl":
            self.open_playlist(arg)

    # ---------- threads de fundo ----------
    def poll(self):
        tick = 0
        while not self.closing:
            time.sleep(0.5)
            tick += 1
            c = self.cast
            try:
                if self.sleep_at and time.time() >= self.sleep_at:
                    self.sleep_at, self.armed = None, False
                    self.ui(lambda: self.sleep_cb.set(T("sleep_off")))
                    self.msg(T("timer_up"))
                    c and c.media_controller.stop()
                if not c:
                    continue
                if tick % 6 == 0 and not getattr(c, "is_pc", False):
                    ok = bool(c.socket_client.is_connected)
                    self.set_online(ok)
                    self.watch_connection(ok)
                ms = c.media_controller.status
                self.playing = bool(ms and ms.player_state == "PLAYING")
                if self.playing != self._shown_playing:
                    self._shown_playing = self.playing
                    self.ui(lambda pl=self.playing: self.play_btn.config(icon="pause" if pl else "play"))
                if tick % 4 == 0 and not self.vol_drag:
                    lv = c.status.volume_level if c.status else None
                    if lv is not None:
                        self.vol_val = lv * 100
                        self.ui(lambda v=lv: (self.vol.set(v * 100), self.vol_lbl.config(text=f"{int(v * 100)}%")))
                if ms and ms.player_state in ("PLAYING", "PAUSED", "BUFFERING"):
                    self.pos = ms.adjusted_current_time or 0
                    self.dur_now = ms.duration or self.dur or 0
                    if tick % 2 == 0:
                        self.ui(lambda p=self.pos, d=self.dur_now: self.set_timeline(p, d))
                    lead = max(0.3, self.latency + 0.4 + self.adjust)
                    if self.armed and self.playing and self.dur_now and self.dur_now - self.pos <= lead:
                        self.try_early()
                if tick % 30 == 0 and self.playing:
                    self.save_session()
            except Exception:
                log(traceback.format_exc())

    def downloader(self):
        """Baixa as próximas músicas (ou a fila toda) em segundo plano, devagar."""
        while not self.closing:
            time.sleep(2)
            try:
                if not self.tools or time.time() < self.blocked_until or not (self.cast or self.bulk):
                    continue
                n = len(self.tracks)
                if self.bulk:
                    order = list(range(self.idx + 1, n)) + list(range(0, self.idx + 1))
                else:
                    order = list(range(self.idx + 1, min(self.idx + 1 + self.lookahead, n)))
                did = False
                for j in order:
                    t = self.tracks[j]
                    if tkey(t) in self.failed or self.offline_info(t):
                        continue
                    did = True
                    try:
                        self.get_info(t, quiet=True)
                    except Blocked:
                        pass
                    except Exception as e:
                        self.failed.add(tkey(t))
                        self.msg(T("play_fail", t=t["title"], e=str(e)[:120]))
                    self.update_dl()
                    self.refresh_usage()
                    break
                if not did and not self.bulk and self.cast and visuals is not None and self.idx + 1 < n:
                    nx = self.offline_info(self.tracks[self.idx + 1])
                    if nx and nx.get("ctype", "").startswith("audio"):
                        self.visual_for(nx, quiet=True)  # deixa a tela da próxima música pronta
                if self.bulk:
                    if self.over_limit():
                        self.stop_bulk(T("bulk_limit"))
                    elif not did:
                        ready = sum(1 for t in self.tracks if self.offline_info(t))
                        self.stop_bulk(T("bulk_done", r=ready, n=len(self.tracks), f=len(self.failed)))
            except Exception:
                log(traceback.format_exc())

    def on_close(self):
        if self.closing:
            return
        self.closing = True
        try:
            self.withdraw()  # some na hora; o resto da limpeza acontece sem a pessoa esperar
        except Exception:
            pass
        for fn in (self.save_files_ui, self.save_session):
            try:
                fn()
            except Exception:
                log(traceback.format_exc())
        try:
            if self.pcdev:
                self.pcdev.close_window()
        except Exception:
            pass
        if self.browser:  # a busca de TVs às vezes demora a parar: espera no máximo 2 s
            th = threading.Thread(target=lambda: self.browser.stop_discovery(), daemon=True)
            th.start()
            th.join(2)
        self.destroy()


def scan_chromecasts():
    """Varre a rede local procurando aparelhos com a porta do Chromecast (8009)."""
    import socket
    from concurrent.futures import ThreadPoolExecutor
    base = ".".join(lan_ip().split(".")[:3])

    def check(i):
        ip = f"{base}.{i}"
        try:
            with socket.create_connection((ip, 8009), timeout=0.6):
                return ip
        except Exception:
            return None
    with ThreadPoolExecutor(64) as ex:
        return [ip for ip in ex.map(check, range(1, 255)) if ip]


def single_instance():
    """Só um Livingplay aberto por vez (dois ao mesmo tempo brigariam pela mesma pasta e configuração).
    Devolve o arquivo de trava (mantido aberto) ou None se já houver outro aberto."""
    path = os.path.join(HOME, "." + APP_SLUG + ".lock")
    try:
        f = open(path, "a+")
        f.seek(0)
        if sys.platform.startswith("win"):
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except OSError:
        return None
    except Exception:  # sem como travar neste sistema: segue normalmente
        return True


if __name__ == "__main__":
    enable_dpi()
    _lock = single_instance()
    if _lock is None:
        from tkinter import messagebox
        r = tk.Tk()
        r.withdraw()
        set_lang(load_cfg().get("lang") or detect_lang())
        messagebox.showinfo(APP_NAME, T("already_open"), parent=r)
        r.destroy()
        sys.exit(0)
    App().mainloop()
    os._exit(0)  # tudo já foi salvo; encerra também as tarefas de fundo que ainda estiverem rodando
