"""Componentes visuais próprios: botões arredondados, ícones vetoriais, controle segmentado e etiqueta de status.
Tudo é desenhado em Canvas, então fica igual em qualquer Windows (sem depender de fontes de símbolos)."""
import base64
import io
import math
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

try:  # Pillow é opcional: com ele os botões e ícones saem suavizados (anti-aliasing); sem ele, o desenho antigo
    from PIL import Image, ImageDraw
    AA_OK = True
except Exception:  # pragma: no cover
    AA_OK = False

UI = {"pal": None, "u": 1.0, "fam": "Segoe UI", "fs": 9}
_FONTS = {}


def px(v):
    return max(1, int(round(v * UI["u"])))


def font(delta=0, bold=False):
    root = tk._default_root
    key = (id(root), UI["fam"], UI["fs"] + delta, bold)
    if key not in _FONTS:
        _FONTS[key] = tkfont.Font(root=root, family=UI["fam"], size=UI["fs"] + delta, weight="bold" if bold else "normal")
    return _FONTS[key]


def _rgb(c):
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def mix(a, b, t):
    """Mistura duas cores (t=0 -> a, t=1 -> b)."""
    ra, rb = _rgb(a), _rgb(b)
    return "#%02x%02x%02x" % tuple(int(ra[i] + (rb[i] - ra[i]) * t) for i in range(3))


def _rrect_tk(c, x1, y1, x2, y2, r, **kw):
    r = max(1, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2, x1, y2,
           x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def rrect(c, x1, y1, x2, y2, r, **kw):
    """Retângulo arredondado suavizado (cai no desenho simples do Tk se o Pillow não estiver disponível)."""
    if AA_OK and isinstance(c, tk.Canvas):
        try:
            ox, oy = int(math.floor(x1)) - 1, int(math.floor(y1)) - 1
            a = _AA(c, math.ceil(x2) - ox + 2, math.ceil(y2) - oy + 2, ox, oy)
            r = max(1, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
            a.rrect(x1, y1, x2, y2, r, kw.get("fill", ""), kw.get("outline", ""), kw.get("width", 1))
            return a.flush()
        except Exception:
            pass
    return _rrect_tk(c, x1, y1, x2, y2, int(r), **kw)


# ---------------------------------------------------------------- desenho suavizado (anti-aliasing)
# O Canvas do Tk não suaviza bordas no Windows (fica "serrilhado"). Aqui cada forma é desenhada 4x maior com
# Pillow, reduzida com filtro de alta qualidade e colocada no Canvas como imagem PNG com transparência.
_SS = 4
_IMG_CACHE = {}


def _col(c):
    return None if c in ("", None) else c


class _AA:
    """Imita os métodos create_* do Canvas que o desenho dos ícones usa, mas gera uma imagem suavizada."""

    def __init__(self, canvas, w, h, ox=0, oy=0):
        self.cv, self.w, self.h, self.ox, self.oy = canvas, max(1, int(w)), max(1, int(h)), ox, oy
        self.ops, self.texts = [], []

    def _r(self, pts):
        return tuple(round(v - (self.ox if i % 2 == 0 else self.oy), 2) for i, v in enumerate(pts))

    # --- formas
    def rrect(self, x1, y1, x2, y2, r, fill="", outline="", width=1):
        self.ops.append(("rr", self._r((x1, y1, x2, y2)), round(r, 2), _col(fill), _col(outline), width))

    def create_polygon(self, *pts, fill="", outline="", width=1, **_k):
        self.ops.append(("pg", self._r(pts), _col(fill), _col(outline), width))

    def create_rectangle(self, x1, y1, x2, y2, fill="", outline="", width=1, **_k):
        self.ops.append(("rc", self._r((x1, y1, x2, y2)), _col(fill)))

    def create_line(self, *pts, fill="", width=1, **_k):
        self.ops.append(("ln", self._r(pts), _col(fill), width))

    def create_arc(self, x1, y1, x2, y2, start=0, extent=90, outline="", width=1, **_k):
        self.ops.append(("ar", self._r((x1, y1, x2, y2)), start, extent, _col(outline), width))

    def create_oval(self, x1, y1, x2, y2, fill="", outline="", **_k):
        self.ops.append(("ov", self._r((x1, y1, x2, y2)), _col(fill)))

    def create_text(self, x, y, **kw):
        self.texts.append((x, y, kw))

    # --- render
    def _render(self):
        S = _SS
        img = Image.new("RGBA", (self.w * S, self.h * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        def dot(x, y, rad, col):
            d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=col)

        for op in self.ops:
            k = op[0]
            if k == "rr":
                _, (x1, y1, x2, y2), r, fill, out, wd = op
                d.rounded_rectangle((x1 * S, y1 * S, x2 * S - 1, y2 * S - 1), radius=r * S, fill=fill, outline=out,
                                    width=int(wd * S) if out else 0)
            elif k == "pg":
                _, pts, fill, out, wd = op
                p = [v * S for v in pts]
                if fill:
                    d.polygon(p, fill=fill)
                if out and wd:
                    ow = max(1, int(wd * S))
                    d.line(p + p[:2], fill=out, width=ow, joint="curve")
                    for i in range(0, len(p), 2):
                        dot(p[i], p[i + 1], ow / 2, out)
            elif k == "rc":
                _, (x1, y1, x2, y2), fill = op
                d.rectangle((x1 * S, y1 * S, x2 * S - 1, y2 * S - 1), fill=fill)
            elif k == "ln":
                _, pts, fill, wd = op
                p = [v * S for v in pts]
                ow = max(1, int(wd * S))
                d.line(p, fill=fill, width=ow, joint="curve")
                dot(p[0], p[1], ow / 2, fill)
                dot(p[-2], p[-1], ow / 2, fill)
            elif k == "ar":
                _, (x1, y1, x2, y2), st, ex, out, wd = op
                d.arc((x1 * S, y1 * S, x2 * S, y2 * S), -(st + ex), -st, fill=out, width=max(1, int(wd * S)))
            elif k == "ov":
                _, (x1, y1, x2, y2), fill = op
                d.ellipse((x1 * S, y1 * S, x2 * S - 1, y2 * S - 1), fill=fill)
        img = img.convert("RGBa").resize((self.w, self.h), Image.LANCZOS).convert("RGBA")
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return base64.b64encode(buf.getvalue())

    def flush(self):
        key = (id(tk._default_root), self.w, self.h, tuple(self.ops))
        ph = _IMG_CACHE.get(key)
        if ph is None:
            if len(_IMG_CACHE) > 800:
                _IMG_CACHE.clear()
            ph = tk.PhotoImage(master=self.cv, data=self._render())
            _IMG_CACHE[key] = ph
        item = self.cv.create_image(self.ox, self.oy, anchor="nw", image=ph)
        for x, y, kw in self.texts:
            self.cv.create_text(x, y, **kw)
        return item



def oval(c, x1, y1, x2, y2, fill="", outline="", width=1):
    """Círculo/elipse suavizado."""
    if AA_OK and isinstance(c, tk.Canvas):
        return rrect(c, x1, y1, x2, y2, min(x2 - x1, y2 - y1) / 2, fill=fill, outline=outline, width=width)
    return c.create_oval(x1, y1, x2, y2, fill=fill, outline=outline, width=width)


def _bbox_aa(c, pts, pad):
    xs, ys = pts[0::2], pts[1::2]
    ox, oy = int(math.floor(min(xs))) - pad, int(math.floor(min(ys))) - pad
    return _AA(c, math.ceil(max(xs)) - ox + pad, math.ceil(max(ys)) - oy + pad, ox, oy)


def aline(c, *pts, fill, width=1):
    """Linha com pontas arredondadas, suavizada."""
    if AA_OK and isinstance(c, tk.Canvas):
        try:
            a = _bbox_aa(c, pts, int(width) + 2)
            a.create_line(*pts, fill=fill, width=width)
            return a.flush()
        except Exception:
            pass
    return c.create_line(*pts, fill=fill, width=width, capstyle="round")


def aarc(c, x1, y1, x2, y2, start, extent, outline, width=1):
    """Arco (só o traço), suavizado."""
    if AA_OK and isinstance(c, tk.Canvas):
        try:
            a = _bbox_aa(c, (x1, y1, x2, y2), int(width) + 2)
            a.create_arc(x1, y1, x2, y2, start=start, extent=extent, outline=outline, width=width)
            return a.flush()
        except Exception:
            pass
    return c.create_arc(x1, y1, x2, y2, start=start, extent=extent, style="arc", outline=outline, width=width)


def hide_title_icon(win):
    """Windows: deixa o ícone da BARRA DE TÍTULO transparente (o ícone da barra de tarefas e do Alt+Tab continua).
    Não faz nada em outros sistemas."""
    import sys
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        from ctypes import wintypes
        u32 = ctypes.windll.user32
        u32.GetParent.argtypes, u32.GetParent.restype = [wintypes.HWND], wintypes.HWND
        u32.CreateIcon.argtypes = [wintypes.HINSTANCE, ctypes.c_int, ctypes.c_int, ctypes.c_ubyte, ctypes.c_ubyte,
                                   ctypes.c_void_p, ctypes.c_void_p]
        u32.CreateIcon.restype = wintypes.HICON
        u32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        u32.SendMessageW.restype = ctypes.c_ssize_t
        win.update_idletasks()
        hwnd = u32.GetParent(win.winfo_id())
        if not hwnd:
            return
        n = 32 * 32 // 8
        and_bits = (ctypes.c_ubyte * n)(*([0xFF] * n))  # máscara AND = 1 e XOR = 0: ícone totalmente transparente
        xor_bits = (ctypes.c_ubyte * n)()
        hicon = u32.CreateIcon(None, 32, 32, 1, 1, ctypes.cast(and_bits, ctypes.c_void_p), ctypes.cast(xor_bits, ctypes.c_void_p))
        if hicon:
            win._blank_icon = hicon
            u32.SendMessageW(hwnd, 0x0080, 0, hicon)  # WM_SETICON, ICON_SMALL (barra de título)
    except Exception:
        pass


def bg_of(widget):
    """Cor de fundo do pai (tk ou ttk), para o botão arredondado 'se fundir' com ele."""
    try:
        return widget.cget("bg")
    except tk.TclError:
        pass
    try:
        from tkinter import ttk
        st = str(widget.cget("style")) or widget.winfo_class()
        return ttk.Style().lookup(st, "background") or UI["pal"]["surface"]
    except Exception:
        return UI["pal"]["surface"]


def draw_icon(c, name, cx, cy, s, col, tag="ic"):
    """Ícones vetoriais suavizados. s = meia altura do ícone em pixels."""
    if AA_OK and isinstance(c, tk.Canvas):
        try:
            m = int(math.ceil(s * 1.6)) + px(3)
            ox, oy = int(cx) - m, int(cy) - m
            a = _AA(c, 2 * m, 2 * m, ox, oy)
            _draw_icon_raw(a, name, cx, cy, s, col, tag)
            return a.flush()
        except Exception:
            pass
    return _draw_icon_raw(c, name, cx, cy, s, col, tag)


def _draw_icon_raw(c, name, cx, cy, s, col, tag="ic"):
    """Ícones vetoriais. s = meia altura do ícone em pixels."""
    w = max(2, px(2))
    kw = dict(fill=col, outline=col, width=1, tags=tag)
    if name == "play":
        c.create_polygon(cx - .45 * s, cy - .65 * s, cx - .45 * s, cy + .65 * s, cx + .65 * s, cy, joinstyle="round",
                         **{**kw, "width": w})
    elif name == "pause":
        for x in (-.5, .15):
            c.create_rectangle(cx + x * s, cy - .6 * s, cx + (x + .35) * s, cy + .6 * s, **kw)
    elif name in ("next", "prev"):
        d = 1 if name == "next" else -1
        c.create_polygon(cx - d * .5 * s, cy - .55 * s, cx - d * .5 * s, cy + .55 * s, cx + d * .35 * s, cy,
                         joinstyle="round", **{**kw, "width": w})
        x1, x2 = sorted((cx + d * .5 * s, cx + d * .68 * s))
        c.create_rectangle(x1, cy - .55 * s, x2, cy + .55 * s, **kw)
    elif name == "stop":
        c.create_rectangle(cx - .5 * s, cy - .5 * s, cx + .5 * s, cy + .5 * s, **kw)
    elif name in ("back10", "fwd10"):
        # conjunto [setas][folga][número] centralizado, usando a largura real do texto (qualquer fonte/escala)
        f = font(-1, True)
        tw = .42 * s                      # largura de cada seta
        aw = .5 * s + tw                  # largura das duas setas juntas
        gap = max(px(4), .4 * s)          # folga entre setas e número
        txw = f.measure("10")
        x0 = cx - (aw + gap + txw) / 2
        if name == "back10":
            for off in (0, .5):
                x = x0 + off * s
                c.create_polygon(x + tw, cy - .5 * s, x + tw, cy + .5 * s, x, cy, joinstyle="round", **{**kw, "width": 1})
            c.create_text(x0 + aw + gap + txw / 2, cy, text="10", fill=col, font=f, tags=tag)
        else:
            c.create_text(x0 + txw / 2, cy, text="10", fill=col, font=f, tags=tag)
            for off in (0, .5):
                x = x0 + txw + gap + off * s
                c.create_polygon(x, cy - .5 * s, x, cy + .5 * s, x + tw, cy, joinstyle="round", **{**kw, "width": 1})
    elif name == "shuffle":
        for sy in (1, -1):
            c.create_line(cx - .7 * s, cy - sy * .45 * s, cx - .2 * s, cy - sy * .45 * s, cx + .25 * s,
                          cy + sy * .45 * s, cx + .5 * s, cy + sy * .45 * s, fill=col, width=w, joinstyle="round",
                          capstyle="round", tags=tag)
            c.create_polygon(cx + .45 * s, cy + sy * .45 * s - .3 * s, cx + .85 * s, cy + sy * .45 * s,
                             cx + .45 * s, cy + sy * .45 * s + .3 * s, **kw)
    elif name == "repeat":
        c.create_line(cx - .7 * s, cy + .1 * s, cx - .7 * s, cy - .4 * s, cx + .3 * s, cy - .4 * s, fill=col,
                      width=w, joinstyle="round", capstyle="round", tags=tag)
        c.create_polygon(cx + .3 * s, cy - .7 * s, cx + .75 * s, cy - .4 * s, cx + .3 * s, cy - .1 * s, **kw)
        c.create_line(cx + .7 * s, cy - .1 * s, cx + .7 * s, cy + .4 * s, cx - .3 * s, cy + .4 * s, fill=col,
                      width=w, joinstyle="round", capstyle="round", tags=tag)
        c.create_polygon(cx - .3 * s, cy + .1 * s, cx - .75 * s, cy + .4 * s, cx - .3 * s, cy + .7 * s, **kw)
    elif name == "volume":
        c.create_polygon(cx - .85 * s, cy - .3 * s, cx - .45 * s, cy - .3 * s, cx + .05 * s, cy - .7 * s,
                         cx + .05 * s, cy + .7 * s, cx - .45 * s, cy + .3 * s, cx - .85 * s, cy + .3 * s,
                         joinstyle="round", **{**kw, "width": 1})
        for r in (.45, .85):
            c.create_arc(cx + .05 * s - r * s * .5, cy - r * s, cx + .05 * s + r * s * 1.5, cy + r * s, start=-45,
                         extent=90, style="arc", outline=col, width=w, tags=tag)
    elif name == "refresh":
        c.create_arc(cx - .75 * s, cy - .75 * s, cx + .75 * s, cy + .75 * s, start=40, extent=270, style="arc",
                     outline=col, width=w, tags=tag)
        c.create_polygon(cx + .75 * s, cy - .75 * s, cx + .75 * s, cy - .05 * s, cx + .1 * s, cy - .1 * s, **kw)


KINDS = {"TButton": "normal", "Accent.TButton": "accent", "Icon.TButton": "icon", "Play.TButton": "play",
         "Skip.TButton": "skip", "Toggle.TButton": "toggle", "ToggleOn.TButton": "toggleon", "Mini.TButton": "mini"}


class Btn(tk.Canvas):
    """Botão com cantos arredondados, estados (normal, passar o mouse, pressionado, desativado) e foco por teclado."""

    def __init__(self, parent, text="", style="TButton", command=None, icon=None, **_ignored):
        self.pal = UI["pal"]
        self.text, self.style, self.cmd, self.icon = text, style, command, icon
        self.disabled = self.hover = self.down = self.focus = False
        self.w = self.h = 1
        super().__init__(parent, bg=bg_of(parent), highlightthickness=0, bd=0, takefocus=1)
        self._size()
        self.bind("<Configure>", self._conf)
        self.bind("<Enter>", lambda e: self._set(hover=True))
        self.bind("<Leave>", lambda e: self._set(hover=False, down=False))
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<FocusIn>", lambda e: self._set(focus=True))
        self.bind("<FocusOut>", lambda e: self._set(focus=False))
        self.bind("<Key-space>", self._key)
        self.bind("<Return>", self._key)

    # --- tamanho
    @property
    def kind(self):
        return KINDS.get(self.style, "normal")

    def _size(self):
        k = self.kind
        if k == "play":
            w = h = px(58)
        elif k in ("icon", "toggle", "toggleon"):
            w = h = px(40)
        elif k in ("skip",):
            w, h = px(58), px(40)
        else:
            f = font(0, k == "accent")
            pad = (px(18), px(9)) if k == "accent" else (px(14), px(7))
            if k == "mini":
                pad = (px(10), px(4))
            w, h = f.measure(self.text) + 2 * pad[0], f.metrics("linespace") + 2 * pad[1]
        self.w, self.h = w, h
        super().config(width=w, height=h)

    # --- API compatível com ttk.Button
    def config(self, **kw):
        again = False
        for key in ("text", "style", "command", "icon"):
            if key in kw:
                v = kw.pop(key)
                setattr(self, "cmd" if key == "command" else key, v)
                again = again or key in ("text", "style", "icon")
        if "state" in kw:
            self.disabled = kw.pop("state") == "disabled"
        for k in list(kw):
            if k not in self.keys():
                kw.pop(k)
        if kw:
            super().config(**kw)
        if again:
            self._size()
        self.draw()
    configure = config

    def cget(self, key):
        if key == "text":
            return self.text
        if key == "style":
            return self.style
        return super().cget(key)

    def state(self, spec=None):
        if spec is None:
            return ("disabled",) if self.disabled else ()
        for s in spec:
            if s == "disabled":
                self.disabled = True
            elif s == "!disabled":
                self.disabled = False
        self.draw()

    def invoke(self):
        if not self.disabled and self.cmd:
            self.cmd()

    # --- eventos
    def _set(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)
        self.draw()

    def _conf(self, e):
        self.w, self.h = e.width, e.height
        self.draw()

    def _press(self, e):
        if not self.disabled:
            self._set(down=True)

    def _release(self, e):
        was = self.down
        self._set(down=False)
        if was and 0 <= e.x <= self.w and 0 <= e.y <= self.h:
            self.invoke()

    def _key(self, e):
        self.invoke()
        return "break"

    # --- desenho
    def colors(self):
        p, k = self.pal, self.kind
        if k in ("accent", "play"):
            fill, fg, line = p["accent"], p["on_accent"], p["accent"]
            if self.hover:
                fill = line = p["accent2"]
            if self.down:
                fill = line = mix(p["accent"], "#000000", .2)
            if self.disabled:
                fill = line = p["border"]
                fg = p["muted"]
        else:
            fill, fg, line = p["surface2"], p["text"], p["border"]
            if k == "toggle":
                fg = p["muted"]
            if k == "toggleon":
                fill, fg, line = p.get("accent_soft", p["border"]), p["accent"], p["accent"]
            if self.hover:
                fill = mix(fill, p["text"], .07)
            if self.down:
                fill = mix(fill, p["text"], .14)
            if self.disabled:
                fill, fg, line = p["surface"], mix(p["muted"], p["surface"], .35), p["border"]
        return fill, fg, line

    def draw(self):
        self.delete("all")
        w, h, k = self.w, self.h, self.kind
        fill, fg, line = self.colors()
        r = h // 2 if k == "play" else (px(10) if k in ("icon", "toggle", "toggleon", "skip") else px(8))
        edge = self.pal["accent"] if self.focus else line
        lw = 2 if self.focus else 1
        done = False
        if AA_OK:
            try:
                a = _AA(self, w, h)
                a.rrect(1, 1, w - 1, h - 1, r, fill, edge, lw)
                if self.icon:
                    _draw_icon_raw(a, self.icon, w / 2, h / 2, px(11) if k == "play" else px(8), fg)
                a.flush()
                done = True
            except Exception:
                self.delete("all")
        if not done:
            _rrect_tk(self, 1, 1, w - 1, h - 1, r, fill=fill, outline=edge, width=lw)
            if self.icon:
                _draw_icon_raw(self, self.icon, w / 2, h / 2, px(11) if k == "play" else px(8), fg)
        if not self.icon and self.text:
            self.create_text(w / 2, h / 2, text=self.text, fill=fg, font=font(0, k in ("accent", "skip")))
        if self.disabled:
            super().config(cursor="arrow")
        else:
            super().config(cursor="hand2")


class Segmented(tk.Canvas):
    """Controle de 2 ou mais opções lado a lado. Com toggle=True, qualquer clique alterna para a outra opção (switch)."""

    def __init__(self, parent, options, value, command=None, toggle=False, height=32):
        self.pal = UI["pal"]
        self.options, self.value, self.cmd, self.toggle = options, value, command, toggle
        self.hover = None
        f = font(0, True)
        self.pad = px(14)
        self.widths = [f.measure(lab) + 2 * self.pad for _, lab in options]
        self.h = px(height)
        super().__init__(parent, width=sum(self.widths) + 4, height=self.h, bg=bg_of(parent), highlightthickness=0,
                         bd=0, cursor="hand2")
        self.bind("<ButtonRelease-1>", self._click)
        self.bind("<Motion>", self._move)
        self.bind("<Leave>", lambda e: self._hv(None))
        self.draw()

    def _index_at(self, x):
        acc = 2
        for i, w in enumerate(self.widths):
            if x < acc + w:
                return i
            acc += w
        return len(self.widths) - 1

    def _move(self, e):
        self._hv(self._index_at(e.x))

    def _hv(self, i):
        if i != self.hover:
            self.hover = i
            self.draw()

    def _click(self, e):
        i = self._index_at(e.x)
        if self.toggle:
            i = (self.values().index(self.value) + 1) % len(self.options)
        self.select(self.options[i][0], True)

    def values(self):
        return [v for v, _ in self.options]

    def select(self, value, fire=False):
        changed = value != self.value
        self.value = value
        self.draw()
        if fire and changed and self.cmd:
            self.cmd(value)

    def set(self, value):
        self.select(value, False)

    def get(self):
        return self.value

    def draw(self):
        p = self.pal
        self.delete("all")
        W = sum(self.widths) + 4
        rrect(self, 1, 1, W - 1, self.h - 1, self.h // 2, fill=p["surface2"], outline=p["border"])
        x = 2
        for i, ((val, lab), w) in enumerate(zip(self.options, self.widths)):
            on = val == self.value
            if on:
                rrect(self, x + 1, 3, x + w - 1, self.h - 3, (self.h - 6) // 2, fill=p["accent"], outline=p["accent"])
            elif self.hover == i and not self.toggle:
                rrect(self, x + 1, 3, x + w - 1, self.h - 3, (self.h - 6) // 2, fill=mix(p["surface2"], p["text"], .07),
                      outline=mix(p["surface2"], p["text"], .07))
            self.create_text(x + w / 2, self.h / 2, text=lab, font=font(0, True),
                             fill=p["on_accent"] if on else p["muted"])
            x += w


class Pill(tk.Canvas):
    """Etiqueta arredondada com uma bolinha colorida e um texto (status da conexão)."""

    def __init__(self, parent):
        self.pal = UI["pal"]
        self.text, self.color = "", self.pal["warn"]
        super().__init__(parent, bg=bg_of(parent), highlightthickness=0, bd=0, height=px(32))
        self.set("...", self.pal["warn"])

    def set(self, text, color):
        self.text, self.color = text, color
        f = font(0, True)
        w = f.measure(text) + px(44)
        super().config(width=w, height=px(32))
        self.draw(w)

    def draw(self, w=None):
        p = self.pal
        w = w or int(self["width"])
        h = px(32)
        self.delete("all")
        rrect(self, 1, 1, w - 1, h - 1, h // 2, fill=p["surface"], outline=p["border"])
        r = px(5)
        rrect(self, px(14) - r, h / 2 - r, px(14) + r, h / 2 + r, r, fill=self.color, outline=self.color)
        self.create_text(px(26), h / 2, text=self.text, anchor="w", font=font(0, True), fill=p["text"])


class Logo(tk.Canvas):
    """Marca do programa: usa os PNGs do ícone (assets/png). Se não achar, desenha uma versão simplificada."""
    SIZES = (16, 20, 24, 32, 40, 48, 64, 80, 96, 128, 256, 512)

    def __init__(self, parent, size=34):
        self.pal = UI["pal"]
        s = px(size)
        self.img = None
        try:
            import os
            base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
            if AA_OK:  # mesmo desenho em qualquer tamanho: reduz o arquivo-mestre com filtro de alta qualidade
                im = Image.open(os.path.join(base, "icon_master.png")).convert("RGBa")
                im = im.resize((s, s), Image.LANCZOS).convert("RGBA")
                buf = io.BytesIO()
                im.save(buf, "PNG")
                self.img = tk.PhotoImage(master=tk._default_root, data=base64.b64encode(buf.getvalue()))
            else:
                n = min(self.SIZES, key=lambda v: abs(v - s))
                self.img = tk.PhotoImage(master=tk._default_root, file=os.path.join(base, "png", f"icon_{n}.png"))
                s = n
        except Exception:
            self.img = None
        super().__init__(parent, width=s, height=s, bg=bg_of(parent), highlightthickness=0, bd=0)
        if self.img is not None:
            self.create_image(s // 2, s // 2, image=self.img)
            return
        p = self.pal
        rrect(self, 1, 1, s - 1, s - 1, s // 4, fill=p["accent"], outline=p["accent"])
        w = max(2, px(2))
        rrect(self, s * .2, s * .25, s * .8, s * .68, px(4), fill="", outline="white", width=w)
        self.create_polygon(s * .43, s * .35, s * .43, s * .58, s * .62, s * .465, fill="white", outline="white",
                            width=1, joinstyle="round")


class Chevron(tk.Canvas):
    """Seta de seção recolhível (aberta ▾ / fechada ▸), desenhada e suavizada. config(text="▾"|"▸") troca o estado."""

    def __init__(self, parent, color, bg, size=14):
        s = px(size)
        super().__init__(parent, width=s + px(8), height=s + px(8), bg=bg, highlightthickness=0, bd=0)
        self.col, self.s, self.open = color, s, True
        self.draw()

    def config(self, text=None, **kw):
        if text is not None:
            self.open = text == "\u25be"
            self.delete("all")
            self.draw()
        if kw:
            super().config(**kw)
    configure = config

    def draw(self):
        W = int(self["width"])
        H = int(self["height"])
        cx, cy, t = W / 2, H / 2, self.s * .22
        if self.open:
            pts = (cx - t * 1.2, cy - t * .6, cx + t * 1.2, cy - t * .6, cx, cy + t * .9)
        else:
            pts = (cx - t * .6, cy - t * 1.2, cx - t * .6, cy + t * 1.2, cx + t * .9, cy)
        a = _AA(self, W, H)
        a.create_polygon(*pts, fill=self.col, outline=self.col, width=1)
        a.flush()


class ScrollBox(tk.Frame):
    """Área com rolagem vertical: o conteúdo (self.inner) ocupa sempre a largura toda, uma seção embaixo da outra."""

    def __init__(self, parent, bg, height=300):
        super().__init__(parent, bg=bg)
        self.cv = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0, height=height, width=10)
        self.sb = ttk.Scrollbar(self, orient="vertical", command=self.cv.yview)
        self.cv.configure(yscrollcommand=self._set)
        self.cv.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.cv, bg=bg)
        self.win = self.cv.create_window(0, 0, window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self._upd())
        self.cv.bind("<Configure>", self._resize)
        for w in (self.cv, self.inner):
            w.bind("<Enter>", self._on, add="+")
            w.bind("<Leave>", self._off, add="+")
        self._shown = False

    def _set(self, a, b):
        self.sb.set(a, b)
        need = float(a) > 0.0 or float(b) < 1.0
        if need and not self._shown:
            self.sb.pack(side="right", fill="y")
            self._shown = True
        elif not need and self._shown:
            self.sb.pack_forget()
            self._shown = False

    def _upd(self):
        self.cv.configure(scrollregion=(0, 0, self.inner.winfo_reqwidth(), self.inner.winfo_reqheight()))

    def _resize(self, e):
        self.cv.itemconfigure(self.win, width=e.width)

    def _wheel(self, e):
        if self.inner.winfo_reqheight() <= self.cv.winfo_height():
            return
        step = -1 * (e.delta // 120) if e.delta else (1 if e.num == 5 else -1)
        self.cv.yview_scroll(step * 3, "units")

    def _on(self, _e=None):
        top = self.winfo_toplevel()
        top.bind_all("<MouseWheel>", self._wheel)
        top.bind_all("<Button-4>", self._wheel)
        top.bind_all("<Button-5>", self._wheel)

    def _off(self, e=None):
        try:
            x, y = self.winfo_pointerxy()
            if self.winfo_containing(x, y) is not None and str(self.winfo_containing(x, y)).startswith(str(self)):
                return
        except Exception:
            pass
        top = self.winfo_toplevel()
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            top.unbind_all(ev)
