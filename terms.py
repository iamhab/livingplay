# -*- coding: utf-8 -*-
"""Boas-vindas da primeira execução: um texto curto e amigável com o combinado de uso."""
import tkinter as tk

from app_info import APP_NAME, APP_VERSION
from i18n import T
from ui_widgets import Btn, ScrollBox, font, px
import winframe


class TermsGate(tk.Toplevel):
    """Boas-vindas de uma vez só. Qualquer forma de fechar conta como "Vamos lá"."""

    def __init__(self, app):
        p = app.pal
        super().__init__(app, bg=p["bg"])
        self.accepted = False
        self.title(T("terms_title"))
        self.transient(app)
        self.resizable(False, False)
        W = px(560)
        fl = winframe.begin(self, app, APP_NAME, controls=("close",), close=self._accept)
        tk.Label(self, text=T("terms_head"), bg=p["bg"], fg=p["text"], font=font(4, True),
                 wraplength=W - px(60), justify="left").pack(anchor="w", padx=px(30), pady=(px(22), px(8)))
        tk.Label(self, text=T("terms_body"), bg=p["bg"], fg=p["muted"], font=font(0),
                 wraplength=W - px(60), justify="left").pack(anchor="w", padx=px(30))
        nav = tk.Frame(self, bg=p["bg"])
        nav.pack(side="bottom", fill="x", padx=px(30), pady=px(18))
        self.b_ok = Btn(nav, text=T("terms_ok"), style="Accent.TButton", command=self._accept)
        self.b_ok.pack(side="right")
        self.protocol("WM_DELETE_WINDOW", self._accept)
        self.bind("<Escape>", lambda e: self._accept())
        self.bind("<Return>", lambda e: self._accept())
        winframe.show(self, app, fl, W)  # altura conforme o texto (nada cortado em nenhum idioma ou escala)
        try:
            self.update()
            self.grab_set()
        except Exception:
            pass

    def _accept(self):
        self.accepted = True
        self.destroy()


class NoticeDialog(tk.Toplevel):
    """Avisos e informações legais: só aparece quando a pessoa clica no botão discreto "Avisos" do rodapé."""

    def __init__(self, app):
        p = app.pal
        super().__init__(app, bg=p["bg"])
        self.title(T("notice_title"))
        self.transient(app)
        self.resizable(False, False)
        fl = winframe.begin(self, app, APP_NAME)
        W = px(600)
        pad = px(30)
        nav = tk.Frame(self, bg=p["bg"])
        nav.pack(side="bottom", fill="x", padx=pad, pady=px(16))
        Btn(nav, text=T("notice_close"), style="Accent.TButton", command=self.destroy).pack(side="right")
        tk.Label(self, text=T("notice_title"), bg=p["bg"], fg=p["text"], font=font(5, True), anchor="w",
                 justify="left").pack(anchor="w", padx=pad, pady=(px(24), 0))
        tk.Label(self, text=f"{APP_NAME} {APP_VERSION}  ·  MIT", bg=p["bg"], fg=p["accent"], font=font(-1, True),
                 anchor="w").pack(anchor="w", padx=pad, pady=(px(2), px(10)))
        tk.Frame(self, bg=p["border"], height=1).pack(fill="x", padx=pad)
        box = ScrollBox(self, p["bg"], height=px(200))  # texto longo: rola em vez de ser cortado
        box.pack(fill="both", expand=True, padx=(pad, px(10)), pady=(px(8), 0))
        body = box.inner
        for block in T("notice_body").split("\n\n"):
            head, _, text = block.partition("\n")
            tk.Label(body, text=head, bg=p["bg"], fg=p["text"], font=font(0, True), anchor="w",
                     justify="left").pack(anchor="w", pady=(px(10), px(1)))
            tk.Label(body, text=text, bg=p["bg"], fg=p["muted"], font=font(0), wraplength=W - 2 * pad - px(16),
                     justify="left", anchor="w").pack(anchor="w")
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        box.cv.configure(height=min(body.winfo_reqheight(), int(self.winfo_screenheight() * 0.58)))
        winframe.show(self, app, fl, W)
