# -*- coding: utf-8 -*-
"""Tutorial curto e visual (8 passos), aberto pelo botão "Ver tutorial". Cada passo tem um desenho simples."""
import tkinter as tk
import winframe

from i18n import T
from ui_widgets import UI, Btn, draw_icon, font, mix, px, rrect, oval, aline, aarc

STEPS = 8


# ---------- desenhos (todos usam a paleta atual) ----------
def _card(c, x1, y1, x2, y2, r=10, fill=None, outline=None):
    p = UI["pal"]
    return rrect(c, x1, y1, x2, y2, px(r), fill=fill or p["surface"], outline=outline or p["border"])


def _btn(c, x1, y1, x2, y2, text, accent=False):
    p = UI["pal"]
    rrect(c, x1, y1, x2, y2, px(9), fill=p["accent"] if accent else p["surface2"], outline=p["accent"] if accent else p["border"])
    c.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, font=font(-1, True), fill=p["on_accent"] if accent else p["text"])


def _tv(c, cx, cy, w, h, col=None, label=None):
    p = UI["pal"]
    col = col or p["text"]
    rrect(c, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, px(7), fill=p["surface"], outline=col, width=px(2))
    aline(c, cx - w * .18, cy + h / 2 + px(8), cx + w * .18, cy + h / 2 + px(8), fill=col, width=px(2))
    if label:
        c.create_text(cx, cy, text=label, font=font(-1, True), fill=p["muted"])


def _wifi(c, cx, cy, s, col):
    for i, r in enumerate((.5, 1.0, 1.5)):
        aarc(c, cx - s * r, cy - s * r, cx + s * r, cy + s * r, 45, 90, col, px(2))
    oval(c, cx - px(2), cy - px(2), cx + px(2), cy + px(2), fill=col, outline=col)


def d1(c, W, H):  # achar e conectar
    p = UI["pal"]
    _tv(c, W * .2, H * .45, px(110), px(70), label="TV")
    _wifi(c, W * .2, H * .15 + px(8), px(18), p["accent"])
    _card(c, W * .42, px(24), W - px(24), H - px(24))
    items = ("Sala", "Quarto")
    for i, name in enumerate(items):
        y = px(48) + i * px(42)
        on = i == 0
        rrect(c, W * .42 + px(10), y, W - px(34), y + px(32), px(8), fill=p["accent_soft"] if on else p["surface"],
              outline=p["accent"] if on else p["border"])
        oval(c, W * .42 + px(22), y + px(11), W * .42 + px(32), y + px(21), fill=p["ok"] if on else p["muted"], outline="")
        c.create_text(W * .42 + px(44), y + px(16), text=name, anchor="w", font=font(0, on), fill=p["text"])
    _btn(c, W * .42 + px(10), H - px(70), W * .42 + px(130), H - px(40), T("b_connect"), True)


def d2(c, W, H):  # adicionar vídeos
    p = UI["pal"]
    _card(c, px(24), px(24), W - px(24), H - px(24))
    rrect(c, px(40), px(44), W - px(40), px(78), px(8), fill=p["surface2"], outline=p["border"])
    c.create_text(px(54), px(61), text="https://exemplo.com/video…", anchor="w", font=font(0), fill=p["muted"])
    _btn(c, px(40), px(96), px(170), px(128), T("btn_playnow"), True)
    _btn(c, px(182), px(96), px(262), px(128), T("btn_queue"))
    _btn(c, px(274), px(96), px(400), px(128), T("btn_files"))
    for i in range(2):
        y = px(146) + i * px(24)
        c.create_text(px(48), y + px(9), text=f"{i + 1}.", anchor="w", font=font(-1), fill=p["muted"])
        rrect(c, px(70), y + px(4), W - px(60) - i * px(90), y + px(14), px(5), fill=p["surface2"], outline="")


def d3(c, W, H):  # controles
    p = UI["pal"]
    _card(c, px(24), px(24), W - px(24), H - px(24))
    rrect(c, px(46), px(52), W - px(46), px(58), px(3), fill=p["surface2"], outline="")
    rrect(c, px(46), px(52), px(46) + (W - px(92)) * .38, px(58), px(3), fill=p["accent"], outline="")
    oval(c, px(46) + (W - px(92)) * .38 - px(7), px(55) - px(7), px(46) + (W - px(92)) * .38 + px(7), px(55) + px(7),
                  fill=p["accent"], outline="")
    names = ("shuffle", "prev", "back10", "play", "fwd10", "next", "repeat", "stop")
    gap = (W - px(92)) / len(names)
    for i, n in enumerate(names):
        cx = px(46) + gap * (i + .5)
        big = n == "play"
        r = px(21) if big else px(16)
        rrect(c, cx - r, H * .62 - r, cx + r, H * .62 + r, px(10), fill=p["accent"] if big else p["surface2"], outline="")
        draw_icon(c, n, cx, H * .62, px(8), p["on_accent"] if big else p["text"])
    draw_icon(c, "volume", px(60), H - px(46), px(8), p["muted"])
    rrect(c, px(80), H - px(49), px(220), H - px(43), px(3), fill=p["surface2"], outline="")
    rrect(c, px(80), H - px(49), px(150), H - px(43), px(3), fill=p["accent"], outline="")


def d4(c, W, H):  # Chromecast <-> Computador
    p = UI["pal"]
    _tv(c, W * .11, H * .46, px(84), px(56), label="TV")
    # monitor
    cx, cy = W * .89, H * .46
    rrect(c, cx - px(44), cy - px(30), cx + px(44), cy + px(24), px(6), fill=p["surface"], outline=p["text"], width=px(2))
    aline(c, cx, cy + px(24), cx, cy + px(38), fill=p["text"], width=px(2))
    aline(c, cx - px(22), cy + px(38), cx + px(22), cy + px(38), fill=p["text"], width=px(3))
    c.create_text(cx, cy - px(4), text="PC", font=font(-1, True), fill=p["muted"])
    # chave
    sw_w = px(200)
    x0, y0 = W / 2 - sw_w / 2, H * .46 - px(16)
    rrect(c, x0, y0, x0 + sw_w, y0 + px(32), px(16), fill=p["surface2"], outline=p["border"])
    rrect(c, x0 + px(3), y0 + px(3), x0 + sw_w / 2, y0 + px(29), px(13), fill=p["accent"], outline="")
    c.create_text(x0 + sw_w * .25, y0 + px(16), text=T("tgt_cast"), font=font(-1, True), fill=p["on_accent"])
    c.create_text(x0 + sw_w * .75, y0 + px(16), text=T("tgt_pc"), font=font(-1, True), fill=p["muted"])
    c.create_line(x0 + px(8), H * .46 + px(34), x0 + sw_w - px(8), H * .46 + px(34), fill=p["muted"], arrow="both", width=px(2))


def d5(c, W, H):  # saída de áudio
    p = UI["pal"]
    _card(c, px(24), px(24), W - px(24), H - px(24))
    for k, (cx, lab) in enumerate(((W * .3, T("tgt_cast")), (W * .7, T("tgt_pc")))):
        on = k == 0
        rrect(c, cx - px(70), px(44), cx + px(70), px(120), px(12), fill=p["accent_soft"] if on else p["surface2"],
              outline=p["accent"] if on else p["border"], width=px(2) if on else 1)
        draw_icon(c, "volume", cx, px(72), px(13), p["accent"] if on else p["muted"])
        c.create_text(cx, px(102), text=lab, font=font(-1, True), fill=p["text"])
    c.create_text(W / 2, H - px(48), text="1", font=font(-1), fill=p["muted"], tags="x")
    c.delete("x")
    rrect(c, px(60), H - px(52), W - px(60), H - px(46), px(3), fill=p["surface2"], outline="")
    rrect(c, px(60), H - px(52), W * .55, H - px(46), px(3), fill=p["accent"], outline="")


def d6(c, W, H):  # celular
    p = UI["pal"]
    cx = W * .5
    rrect(c, cx - px(52), px(14), cx + px(52), H - px(14), px(16), fill=p["surface"], outline=p["text"], width=px(2))
    rrect(c, cx - px(40), px(32), cx + px(40), px(60), px(6), fill=p["surface2"], outline="")
    for i in range(3):
        x = cx - px(34) + i * px(25)
        rrect(c, x, px(74), x + px(20), px(94), px(7), fill=p["accent"] if i == 1 else p["surface2"], outline="")
    rrect(c, cx - px(40), px(108), cx + px(40), px(114), px(3), fill=p["surface2"], outline="")
    rrect(c, cx - px(40), px(108), cx + px(8), px(114), px(3), fill=p["accent"], outline="")
    # QR estilizado
    qx, qy, q = W * .15, H * .5 - px(38), px(76)
    _card(c, qx, qy, qx + q, qy + q, 8)
    import random
    rnd = random.Random(7)
    n = 7
    cell = (q - px(16)) / n
    for i in range(n):
        for j in range(n):
            if rnd.random() > .45 or (i < 2 and j < 2) or (i < 2 and j > 4) or (i > 4 and j < 2):
                c.create_rectangle(qx + px(8) + i * cell, qy + px(8) + j * cell, qx + px(8) + (i + 1) * cell - 1,
                                   qy + px(8) + (j + 1) * cell - 1, fill=p["text"], outline="")
    _wifi(c, W * .84, H * .5, px(16), p["accent"])


def d7(c, W, H):  # vídeos guardados e cache
    p = UI["pal"]
    _card(c, px(24), px(24), W - px(24), H - px(24))
    c.create_text(px(44), px(46), text="3,4 GB / 10 GB", anchor="w", font=font(0, True), fill=p["text"])
    rrect(c, px(44), px(64), W - px(44), px(78), px(7), fill=p["surface2"], outline="")
    rrect(c, px(44), px(64), px(44) + (W - px(88)) * .34, px(78), px(7), fill=p["accent"], outline="")
    _btn(c, px(44), px(98), px(190), px(130), T("b_clean"))
    _btn(c, px(202), px(98), px(400), px(130), T("b_delvids"))


def d8(c, W, H):  # ajustes
    p = UI["pal"]
    _card(c, px(24), px(24), W - px(24), H - px(24))
    rows = (("TV", .62), ("", .35), ("", .8))
    for i, (_, f) in enumerate(rows):
        y = px(54) + i * px(36)
        draw_icon(c, "refresh" if i == 0 else "volume", px(50), y, px(8), p["muted"])
        rrect(c, px(76), y - px(3), W - px(52), y + px(3), px(3), fill=p["surface2"], outline="")
        rrect(c, px(76), y - px(3), px(76) + (W - px(128)) * f, y + px(3), px(3), fill=p["accent"], outline="")
        x = px(76) + (W - px(128)) * f
        oval(c, x - px(8), y - px(8), x + px(8), y + px(8), fill=p["surface"], outline=p["accent"], width=px(2))
    seg_x = W / 2 - px(60)
    rrect(c, seg_x, H - px(70), seg_x + px(120), H - px(42), px(14), fill=p["surface2"], outline=p["border"])
    rrect(c, seg_x + px(3), H - px(67), seg_x + px(60), H - px(45), px(11), fill=p["accent"], outline="")


DRAW = [d1, d2, d3, d4, d5, d6, d7, d8]


class Tutorial(tk.Toplevel):
    def __init__(self, app):
        p = app.pal
        super().__init__(app, bg=p["bg"])
        self.app = app
        self.n = 0
        self.title(T("tut_title"))
        self.transient(app)
        self.resizable(False, False)
        W, H = px(580), px(480)
        fl = winframe.begin(self, app, T("tut_title"))
        if fl:
            H += px(44)
        self.stage = tk.Canvas(self, width=px(520), height=px(200), bg=p["bg"], highlightthickness=0, bd=0)
        self.stage.pack(padx=px(30), pady=(px(22), px(6)))
        self.step_lbl = tk.Label(self, bg=p["bg"], fg=p["accent"], font=font(-1, True))
        self.step_lbl.pack()
        self.head = tk.Label(self, bg=p["bg"], fg=p["text"], font=font(4, True), wraplength=px(500), justify="center")
        self.head.pack(pady=(px(4), px(6)))
        self.body = tk.Label(self, bg=p["bg"], fg=p["muted"], font=font(1), wraplength=px(500), justify="center")
        self.body.pack(padx=px(30))
        self.dots = tk.Canvas(self, height=px(16), bg=p["bg"], highlightthickness=0, bd=0)
        self.dots.pack(fill="x", pady=(px(14), px(4)))
        nav = tk.Frame(self, bg=p["bg"])
        nav.pack(side="bottom", fill="x", padx=px(30), pady=px(18))
        self.b_prev = Btn(nav, text=T("tut_prev"), command=lambda: self.go(-1))
        self.b_prev.pack(side="left")
        self.b_next = Btn(nav, text=T("tut_next"), style="Accent.TButton", command=lambda: self.go(1))
        self.b_next.pack(side="right")
        self.b_close = Btn(nav, text=T("tut_close"), command=self.destroy)
        self.b_close.pack(side="right", padx=(0, px(8)))
        self.bind("<Left>", lambda e: self.go(-1))
        self.bind("<Right>", lambda e: self.go(1))
        self.bind("<Escape>", lambda e: self.destroy())
        self.show()
        winframe.show(self, app, fl, W, H)

    def go(self, d):
        n = self.n + d
        if n >= STEPS:
            self.destroy()
            return
        if 0 <= n < STEPS:
            self.n = n
            self.show()

    def show(self):
        p = self.app.pal
        i = self.n + 1
        c = self.stage
        c.delete("all")
        W, H = int(c["width"]), int(c["height"])
        DRAW[self.n](c, W, H)
        self.step_lbl.config(text=T("tut_step", i=i, n=STEPS))
        self.head.config(text=T(f"tut{i}_t"))
        self.body.config(text=T(f"tut{i}_d"))
        self.b_prev.config(state="normal" if self.n else "disabled")
        self.b_next.config(text=T("tut_done") if self.n == STEPS - 1 else T("tut_next"))
        d = self.dots
        d.delete("all")
        w = d.winfo_width() if d.winfo_width() > 1 else px(520)
        gap = px(18)
        x0 = w / 2 - gap * (STEPS - 1) / 2
        for k in range(STEPS):
            on = k == self.n
            r = px(4) if not on else px(5)
            oval(d, x0 + k * gap - r, px(8) - r, x0 + k * gap + r, px(8) + r,
                          fill=p["accent"] if on else mix(p["bg"], p["muted"], .45), outline="")
