# -*- coding: utf-8 -*-
"""Barra de título própria: remove a barra do Windows e desenha minimizar / maximizar / fechar dentro da janela.

Só é usada no Windows (ou com LP_FRAME=1, para testes). Se algo der errado, o usuário volta à barra padrão em
Ajustes ("Usar a barra padrão do Windows") ou iniciando com --native.
"""
import os
import sys
import tkinter as tk

from ui_widgets import mix, px, rrect, aline

CUR = ({"h": "size_we", "v": "size_ns", "se": "size_nw_se", "sw": "size_ne_sw"} if sys.platform.startswith("win")
       else {"h": "sb_h_double_arrow", "v": "sb_v_double_arrow", "se": "bottom_right_corner", "sw": "bottom_left_corner"})
BAR_H = 52
EDGE = 6  # largura (px na escala 1.0) da área de redimensionar nas bordas


def wanted(cfg):
    if "--native" in sys.argv or cfg.get("native_frame"):
        return False
    return sys.platform.startswith("win") or os.environ.get("LP_FRAME") == "1"


def _hwnd(win):
    import ctypes
    return ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()


def _work_area(win):
    """Área útil da tela (sem a barra de tarefas) como (x, y, w, h)."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            from ctypes import wintypes
            r = wintypes.RECT()
            if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0):
                return r.left, r.top, r.right - r.left, r.bottom - r.top
        except Exception:
            pass
    return 0, 0, win.winfo_screenwidth(), win.winfo_screenheight()


class Frameless:
    """Controla a janela principal sem a moldura do sistema."""

    def __init__(self, app, pal=None, close=None):
        self.app = app
        self.pal = pal or app.pal
        self.close = close or getattr(app, "on_close", None) or app.destroy
        self.maxed = False
        self.normal = None
        self.drag = None
        self.bar = None
        app.overrideredirect(True)
        if getattr(app, "_is_main", True) and app.winfo_class() == "Tk":
            pass  # o botão da barra de tarefas é ajustado quando a janela é revelada (sem piscar)
        else:
            app.after(60, self.taskbar_button)
        app.bind("<Map>", self._mapped, add="+")

    # ---- botão na barra de tarefas (janela sem moldura não ganha um sozinha)
    def taskbar_button(self, hidden=False):
        if not sys.platform.startswith("win"):
            return
        try:
            import ctypes
            u = ctypes.windll.user32
            h = _hwnd(self.app)
            GWL_EXSTYLE = -20
            ex = u.GetWindowLongW(h, GWL_EXSTYLE)
            ex = (ex & ~0x00000080) | 0x00040000  # sem TOOLWINDOW, com APPWINDOW
            if ex != u.GetWindowLongW(h, GWL_EXSTYLE):
                if hidden:  # janela ainda escondida: troca o estilo sem piscar
                    u.SetWindowLongW(h, GWL_EXSTYLE, ex)
                else:
                    self.app.withdraw()
                    u.SetWindowLongW(h, GWL_EXSTYLE, ex)
                    self.app.after(20, self.app.deiconify)
        except Exception:
            pass

    def _mapped(self, e):
        if e.widget is self.app:
            self.app.after(30, self.taskbar_button)

    # ---- ações
    def minimize(self):
        if sys.platform.startswith("win"):
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(_hwnd(self.app), 6)  # SW_MINIMIZE
                return
            except Exception:
                pass
        try:
            self.app.overrideredirect(False)
            self.app.iconify()
        except Exception:
            pass

    def toggle_max(self):
        a = self.app
        if self.maxed:
            if self.normal:
                a.geometry(self.normal)
            self.maxed = False
        else:
            self.normal = f"{a.winfo_width()}x{a.winfo_height()}+{a.winfo_x()}+{a.winfo_y()}"
            x, y, w, h = _work_area(a)
            a.geometry(f"{w}x{h}+{x}+{y}")
            self.maxed = True
        if self.bar:
            self.bar.refresh()

    # ---- arrastar
    def drag_start(self, e):
        self.drag = (e.x_root - self.app.winfo_x(), e.y_root - self.app.winfo_y())

    def drag_move(self, e):
        if not self.drag:
            return
        a = self.app
        if self.maxed:  # arrastar uma janela maximizada a devolve ao tamanho normal, sob o ponteiro
            self.toggle_max()
            self.drag = (min(a.winfo_width() // 2, px(200)), px(15))
        a.geometry(f"+{e.x_root - self.drag[0]}+{e.y_root - self.drag[1]}")

    def drag_end(self, _e=None):
        self.drag = None

    # ---- redimensionar pelas bordas
    def grips(self):
        a = self.app
        e = px(EDGE)
        spec = (("e", dict(relx=1, rely=0, x=-e, y=px(BAR_H), width=e, relheight=1, height=-px(BAR_H) - e), CUR["h"]),
                ("w", dict(relx=0, rely=0, x=0, y=px(BAR_H), width=e, relheight=1, height=-px(BAR_H) - e), CUR["h"]),
                ("s", dict(relx=0, rely=1, x=e, y=-e, relwidth=1, width=-2 * e, height=e), CUR["v"]),
                ("se", dict(relx=1, rely=1, x=-2 * e, y=-2 * e, width=2 * e, height=2 * e), CUR["se"]),
                ("sw", dict(relx=0, rely=1, x=0, y=-2 * e, width=2 * e, height=2 * e), CUR["sw"]))
        self.gr = []
        for side, place, cur in spec:
            g = tk.Frame(a, bg=a["bg"], cursor=cur, bd=0, highlightthickness=0)
            g.place(**place)
            g.bind("<ButtonPress-1>", lambda ev, s=side: self._rs_start(ev, s))
            g.bind("<B1-Motion>", self._rs_move)
            g.lift()
            self.gr.append(g)

    def _rs_start(self, e, side):
        if self.maxed:
            return
        a = self.app
        self._rs = (side, e.x_root, e.y_root, a.winfo_width(), a.winfo_height(), a.winfo_x(), a.winfo_y())

    def _rs_move(self, e):
        rs = getattr(self, "_rs", None)
        if not rs or self.maxed:
            return
        side, x0, y0, w0, h0, ax, ay = rs
        a = self.app
        mw, mh = a.minsize()
        dx, dy = e.x_root - x0, e.y_root - y0
        w, h, x = w0, h0, ax
        if "e" in side:
            w = max(mw, w0 + dx)
        if "w" in side:
            w = max(mw, w0 - dx)
            x = ax + (w0 - w)
        if "s" in side:
            h = max(mh, h0 + dy)
        a.geometry(f"{w}x{h}+{x}+{ay}")


class CapBtn(tk.Canvas):
    """Botão de controle da janela (minimizar, maximizar/restaurar, fechar): quadrado arredondado, desenho suavizado."""

    def __init__(self, parent, kind, command, pal, size):
        super().__init__(parent, width=size, height=size, bg=pal["bg"], highlightthickness=0, bd=0, cursor="arrow")
        self.kind, self.cmd, self.pal, self.w, self.h = kind, command, pal, size, size
        self.hover = False
        self.maxed = False
        self.bind("<Enter>", lambda e: self._h(True))
        self.bind("<Leave>", lambda e: self._h(False))
        self.bind("<ButtonRelease-1>", lambda e: self.cmd() if 0 <= e.x < self.w and 0 <= e.y < self.h else None)
        self.draw()

    def _h(self, v):
        self.hover = v
        self.draw()

    def draw(self):
        p = self.pal
        self.delete("all")
        close = self.kind == "close"
        bg = p["bg"]
        if self.hover:
            bg = "#e5484d" if close else mix(p["bg"], p["text"], 0.10)
            rrect(self, 1, 1, self.w - 1, self.h - 1, self.h * 0.28, fill=bg)
            fg = "#ffffff" if close else p["text"]
        else:
            fg = p["muted"]
        cx, cy, s = self.w / 2, self.h / 2, self.h * 0.17
        wd = max(1.3, self.h / 24)
        if self.kind == "min":
            aline(self, cx - s, cy, cx + s, cy, fill=fg, width=wd)
        elif self.kind == "max":
            if self.maxed:
                d = s * 0.4
                rrect(self, cx - s + d, cy - s - d, cx + s + d, cy + s - d, 1.5, outline=fg, width=wd)
                rrect(self, cx - s, cy - s + d, cx + s - d, cy + s + d, 1.5, outline=fg, fill=bg, width=wd)
            else:
                rrect(self, cx - s, cy - s, cx + s, cy + s, 1.5, outline=fg, width=wd)
        else:
            aline(self, cx - s, cy - s, cx + s, cy + s, fill=fg, width=wd)
            aline(self, cx - s, cy + s, cx + s, cy - s, fill=fg, width=wd)


class TitleBar(tk.Frame):
    """Primeira linha da janela: marca e botões à esquerda, controles da janela à direita, tudo na mesma linha."""

    def __init__(self, app, fl, controls=("min", "max", "close"), title=None):
        p = fl.pal
        super().__init__(app, bg=p["bg"])
        self.fl, self.p = fl, p
        fl.bar = self
        small = title is not None  # janelas secundárias: barra mais baixa, com o título à esquerda
        size = px(28 if small else 34)
        pad = px(8 if small else 12)
        cmds = {"close": fl.close, "max": fl.toggle_max, "min": fl.minimize}
        self.btns = {}
        for kind in ("close", "max", "min"):
            if kind not in controls:
                continue
            b = CapBtn(self, kind, cmds[kind], p, size)
            b.pack(side="right", anchor="center", pady=pad, padx=(0, px(8 if small else 10) if kind == "close" else 0))
            self.btns[kind] = b
        if not small:
            tk.Frame(self, bg=p["border"], width=1, height=px(22)).pack(side="right", anchor="center", pady=px(18), padx=(px(10), px(8)))
        else:
            from ui_widgets import font
            tk.Label(self, text=title, bg=p["bg"], fg=p["muted"], font=font(-1, True)).pack(side="left", padx=(px(16), 0))
            self.make_draggable()
        self.refresh()

    def make_draggable(self):
        """Arrastar por qualquer área vazia da linha; duplo clique maximiza. Botões e controles ficam de fora."""
        from ui_widgets import Btn, Segmented
        fl = self.fl

        def walk(w):
            if isinstance(w, (Btn, Segmented, CapBtn)):
                return
            if isinstance(w, (tk.Frame, tk.Label, tk.Canvas)):
                w.bind("<ButtonPress-1>", fl.drag_start, add="+")
                w.bind("<B1-Motion>", fl.drag_move, add="+")
                w.bind("<ButtonRelease-1>", fl.drag_end, add="+")
                w.bind("<Double-Button-1>", lambda e: fl.toggle_max(), add="+")
            for c in w.winfo_children():
                walk(c)
        walk(self)

    def refresh(self):
        b = self.btns.get("max")
        if b:
            b.maxed = self.fl.maxed
            b.draw()


def install(app):
    """Chamado uma vez, antes de montar a tela. Devolve o controlador (ou None se a barra padrão for mantida)."""
    if not wanted(app.cfg):
        return None
    try:
        fl = Frameless(app, app.pal, app.on_close)
        app.configure(highlightthickness=1, highlightbackground=app.pal["border"],
                      highlightcolor=app.pal["border"])
        return fl
    except Exception:
        return None


def build_bar(app):
    """Chamado no começo de cada montagem da tela (a tela é refeita ao trocar tema/idioma/tamanho)."""
    fl = getattr(app, "frame", None)
    if not fl:
        return None
    fl.pal = app.pal  # o tema pode ter mudado desde a última montagem
    app.configure(bg=app.pal["bg"], highlightbackground=app.pal["border"], highlightcolor=app.pal["border"])
    bar = TitleBar(app, fl)
    bar.pack(side="top", fill="x")
    fl.grips()
    return bar


def raise_grips(app):
    fl = getattr(app, "frame", None)
    for g in (getattr(fl, "gr", None) or []):
        try:
            g.lift()
        except tk.TclError:
            pass


def begin(win, app, title, controls=("min", "max", "close"), close=None):
    """Primeiro passo de toda janela secundária: esconde a janela enquanto ela é montada (sem piscar) e, com a
    barra própria ligada, põe no topo a mesma barra do programa (título + minimizar/maximizar/fechar).
    Devolve o controlador, ou None quando vale a barra padrão do Windows."""
    win.withdraw()
    fl = None
    if getattr(app, "frame", None):
        try:
            win.overrideredirect(True)
            fl = Frameless(win, app.pal, close or win.destroy)
            win.configure(highlightthickness=1, highlightbackground=app.pal["border"],
                          highlightcolor=app.pal["border"])
            TitleBar(win, fl, controls, title=title).pack(side="top", fill="x")
        except Exception:
            fl = None
    if fl is None:
        try:
            win.attributes("-toolwindow", True)
        except Exception:
            pass
    return fl


def show(win, app, fl, W=None, H=None):
    """Último passo: posiciona no meio do programa, já no tamanho certo, e só então mostra a janela."""
    win.update_idletasks()
    W = W or win.winfo_reqwidth()
    H = H or win.winfo_reqheight()
    try:
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        W, H = min(W, sw), min(H, int(sh * 0.94))
        x = app.winfo_rootx() + (app.winfo_width() - W) // 2
        y = app.winfo_rooty() + max(0, (app.winfo_height() - H) // 3)
        x, y = max(0, min(x, sw - W)), max(0, min(y, sh - H - px(40)))
        win.geometry(f"{W}x{H}+{x}+{y}")
    except Exception:
        win.geometry(f"{W}x{H}")
    if fl:
        fl.taskbar_button(hidden=True)
    win.deiconify()
    win.lift()
    try:
        win.focus_force()
    except Exception:
        pass
