# -*- coding: utf-8 -*-
"""Janelas de pergunta do programa (confirmar / digitar um nome), no mesmo visual do resto: barra própria,
botões arredondados, tema claro/escuro e teclado (Enter confirma, Esc cancela). Substituem as caixas padrão do Tk."""
import tkinter as tk
from tkinter import ttk

from i18n import T
from ui_widgets import Btn, font, px
import winframe


class _Ask(tk.Toplevel):
    def __init__(self, app, title, text, entry=None, yes=None, no=None, danger=False, default_no=False,
                 only_ok=False):
        p = app.pal
        super().__init__(app, bg=p["bg"])
        self.result = None
        self.title(title)
        self.transient(app)
        self.resizable(False, False)
        fl = winframe.begin(self, app, title, controls=("close",), close=self._cancel)
        W = px(460)
        pad = px(26)
        self.entry = None
        nav = tk.Frame(self, bg=p["bg"])
        nav.pack(side="bottom", fill="x", padx=pad, pady=px(18))
        accent = "Accent.TButton"
        self.b_yes = Btn(nav, text=yes or T("dlg_ok"), style=accent, command=self._ok)
        self.b_yes.pack(side="right")
        if not only_ok:
            self.b_no = Btn(nav, text=no or T("dlg_cancel"), command=self._cancel)
            self.b_no.pack(side="right", padx=(0, px(8)))
        if text:
            tk.Label(self, text=text, bg=p["bg"], fg=p["text"], font=font(0), wraplength=W - 2 * pad,
                     justify="left", anchor="w").pack(anchor="w", padx=pad, pady=(px(24), px(4)), fill="x")
        if entry is not None:
            self.var = tk.StringVar(value=entry)
            self.entry = ttk.Entry(self, textvariable=self.var, font=font(1))
            self.entry.pack(fill="x", padx=pad, pady=(px(8), 0))
            self.entry.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._cancel())
        if entry is None:  # Enter confirma, exceto quando o padrão é "Não"
            self.bind("<Return>", lambda e: self._cancel() if default_no and not only_ok else self._ok())
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._first = self.entry or (self.b_no if default_no and not only_ok else self.b_yes)
        winframe.show(self, app, fl, W)
        try:
            self.update()
            self.grab_set()
            self._first.focus_set()
            if self.entry is not None:
                self.entry.select_range(0, "end")
                self.entry.icursor("end")
        except Exception:
            pass

    def _ok(self):
        self.result = self.var.get() if self.entry is not None else True
        self.destroy()

    def _cancel(self):
        self.result = None if self.entry is not None else False
        self.destroy()


def _run(app, **kw):
    d = _Ask(app, **kw)
    app.wait_window(d)
    return d.result


def confirm(app, title, text, yes=None, no=None, default_no=False):
    """Pergunta Sim/Não. Devolve True ou False."""
    return bool(_run(app, title=title, text=text, yes=yes or T("dlg_yes"), no=no or T("dlg_no"),
                     default_no=default_no))


def ask_text(app, title, prompt, initial=""):
    """Pede um texto. Devolve o texto digitado (sem espaços nas pontas) ou None se cancelar/vazio."""
    r = _run(app, title=title, text=prompt, entry=initial or "")
    r = (r or "").strip()
    return r or None


def inform(app, title, text):
    _run(app, title=title, text=text, only_ok=True)


# ---------- lista de atalhos do teclado ----------
# Cada linha: (alternativas, chave do texto). Cada alternativa é uma combinação de teclas.
KEY_GROUPS = (
    ("kg_play", (
        ((("k_space",),), "kd_play"),
        ((("←",), ("→",)), "kd_skip10"),
        ((("Shift", "←"), ("Shift", "→")), "kd_skip30"),
        ((("↑",), ("↓",)), "kd_vol"),
        ((("Ctrl", "→"), ("N",)), "kd_next"),
        ((("Ctrl", "←"), ("P",)), "kd_prev"),
        ((("M",),), "kd_mute"),
        ((("S",),), "kd_stop"),
    )),
    ("kg_win", (
        ((("F1",),), "kd_help"),
        ((("F11",),), "kd_max"),
        ((("Ctrl", "Q"),), "kd_quit"),
    )),
    ("kg_nav", (
        ((("Ctrl", "1–4"),), "kd_tab"),
        ((("Ctrl", "Tab"),), "kd_tabnext"),
        ((("Ctrl", "L"), ("F6",)), "kd_link"),
        ((("Ctrl", "F"),), "kd_search"),
        ((("Ctrl", "O"),), "kd_files"),
        ((("Ctrl", "S"),), "kd_save"),
        ((("Ctrl", "N"),), "kd_newpl"),
        ((("F5",),), "kd_refresh"),
    )),
    ("kg_lists", (
        ((("Enter",),), "kd_enter"),
        ((("Delete",),), "kd_del"),
        ((("F2",),), "kd_rename"),
        ((("Ctrl", "A"),), "kd_all"),
    )),
)


class KeysDialog(tk.Toplevel):
    """Atalhos em duas colunas, cada tecla desenhada como uma tecla de verdade."""

    def __init__(self, app):
        p = app.pal
        super().__init__(app, bg=p["bg"])
        self.title(T("keys_title"))
        self.transient(app)
        self.resizable(False, False)
        fl = winframe.begin(self, app, T("keys_title"), controls=("close",))
        pad = px(28)
        nav = tk.Frame(self, bg=p["bg"])
        nav.pack(side="bottom", fill="x", padx=pad, pady=(px(10), px(20)))
        Btn(nav, text=T("dlg_ok"), style="Accent.TButton", command=self.destroy).pack(side="right")
        tk.Label(nav, text=T("keys_foot"), bg=p["bg"], fg=p["muted"], font=font(-1), justify="left",
                 anchor="w", wraplength=px(560)).pack(side="left", fill="x")
        tk.Label(self, text=T("keys_title"), bg=p["bg"], fg=p["text"], font=font(5, True), anchor="w").pack(
            anchor="w", padx=pad, pady=(px(20), px(14)))
        cols = tk.Frame(self, bg=p["bg"])
        cols.pack(fill="both", expand=True, padx=pad)
        cap = font(-1, True)
        for ci, groups in enumerate((KEY_GROUPS[:2], KEY_GROUPS[2:])):
            col = tk.Frame(cols, bg=p["bg"])
            col.grid(row=0, column=ci, sticky="nw", padx=(0, px(34) if ci == 0 else 0))
            col.columnconfigure(0, minsize=px(150))
            r = 0
            for gi, (gkey, rows) in enumerate(groups):
                tk.Label(col, text=T(gkey).upper(), bg=p["bg"], fg=p["accent"], font=font(-1, True),
                         anchor="w").grid(row=r, column=0, columnspan=2, sticky="w",
                                          pady=(px(14) if gi else 0, px(6)))
                r += 1
                for alts, dkey in rows:
                    kf = tk.Frame(col, bg=p["bg"])
                    kf.grid(row=r, column=0, sticky="w", pady=px(3))
                    for ai, combo in enumerate(alts):
                        if ai:
                            tk.Label(kf, text=T("k_or"), bg=p["bg"], fg=p["muted"], font=font(-2)).pack(
                                side="left", padx=px(5))
                        for ki, k in enumerate(combo):
                            if ki:
                                tk.Label(kf, text="+", bg=p["bg"], fg=p["muted"], font=font(-2)).pack(
                                    side="left", padx=px(2))
                            tk.Label(kf, text=T(k) if k.startswith("k_") else k, bg=p["surface2"], fg=p["text"],
                                     font=cap, padx=px(7), pady=px(1), highlightthickness=1,
                                     highlightbackground=p["border"]).pack(side="left")
                    tk.Label(col, text=T(dkey), bg=p["bg"], fg=p["text"], font=font(0), anchor="w").grid(
                        row=r, column=1, sticky="w", padx=(px(14), 0))
                    r += 1
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<F1>", lambda e: self.destroy())
        winframe.show(self, app, fl)
        try:
            self.update()
            self.grab_set()
        except Exception:
            pass


def show_keys(app):
    d = KeysDialog(app)
    app.wait_window(d)
