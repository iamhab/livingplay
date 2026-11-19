# -*- coding: utf-8 -*-
"""Reprodução no próprio computador.

O vídeo toca numa janela própria (Microsoft Edge ou Google Chrome em modo "aplicativo", com um perfil separado,
sem abas nem barra de endereço). A janela é uma página HTML5 servida pelo próprio programa, em 127.0.0.1, e
conversa com ele por um canal simples (relatório de estado <-> comandos).

PCDevice imita a parte do objeto de transmissão que o programa usa; assim a fila, os controles, a troca
automática de faixa e o controle pelo celular funcionam igual nos dois modos.
"""
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback

from i18n import T


def log(msg):
    try:
        from livingplay import log as _l
        _l(msg)
    except Exception:
        pass


class _Info:
    host = "127.0.0.1"


class _Sock:
    is_connected = True


class MediaStatus:
    def __init__(self, state, idle_reason, pos, dur, vol, ts):
        self.player_state, self.idle_reason = state, idle_reason
        self._pos, self.duration, self.volume_level, self._ts = pos, dur, vol, ts

    @property
    def current_time(self):
        return self._pos

    @property
    def adjusted_current_time(self):
        if self.player_state == "PLAYING":
            t = self._pos + (time.time() - self._ts)
            return min(t, self.duration) if self.duration else t
        return self._pos


class PCMedia:
    def __init__(self, dev):
        self.dev = dev

    @property
    def status(self):
        return self.dev.snapshot()

    def register_status_listener(self, listener):
        if listener not in self.dev.listeners:
            self.dev.listeners.append(listener)

    def play_media(self, url, content_type, title=None, current_time=0, thumb=None, metadata=None, **_):
        self.dev.load(url, content_type, title or "", current_time or 0)

    def block_until_active(self, timeout=30):
        self.dev.wait_loaded(timeout)

    def pause(self):
        self.dev.send({"op": "pause"})
        self.dev.local_state("PAUSED")

    def play(self):
        self.dev.send({"op": "play"})
        self.dev.local_state("PLAYING")

    def stop(self):
        self.dev.send({"op": "stop"})
        self.dev.local_state("IDLE", "CANCELLED")

    def seek(self, t):
        self.dev.send({"op": "seek", "t": float(t)})
        self.dev.local_pos(float(t))


class PCDevice:
    cast_info = _Info()
    socket_client = _Sock()
    is_pc = True

    def __init__(self, base_url_fn, launch=True):
        """base_url_fn() -> URL da página do player (inclui a senha)."""
        self.base_url_fn = base_url_fn
        self.launch_enabled = launch and not os.environ.get("CP_NO_LAUNCH")
        self.lock = threading.RLock()
        self.cmds, self.listeners = [], []
        self.media_controller = PCMedia(self)
        self.proc = None
        self.last_seen = 0.0
        self.state, self.idle_reason, self.pos, self.dur, self.vol, self.ts = "IDLE", None, 0.0, 0.0, 1.0, time.time()
        self.load_id, self.loaded_id, self.loaded_ev, self.load_err = 0, 0, threading.Event(), None
        self.url = ""
        self.profile = os.path.join(os.path.expanduser("~"), ".livingplay_window")
        self.cancel_sent = False

    # ----- mesma interface do aparelho de TV, para o resto do programa -----
    @property
    def status(self):
        return self.snapshot()

    def wait(self, timeout=None):
        return True

    def set_volume(self, v):
        v = max(0.0, min(1.0, float(v)))
        with self.lock:
            self.vol = v
        self.send({"op": "vol", "v": v})

    def disconnect(self, timeout=None):
        self.close_window()

    # ----- estado -----
    def alive(self):
        return time.time() - self.last_seen < 6.0

    def snapshot(self):
        with self.lock:
            if self.state in ("PLAYING", "PAUSED", "BUFFERING") and self.last_seen and not self.alive() \
                    and time.time() - self.ts > 6.0:
                self.state, self.idle_reason = "IDLE", "CANCELLED"   # janela fechada pelo usuário: não avança a fila
                self.cancel_sent = True
            return MediaStatus(self.state, self.idle_reason, self.pos, self.dur, self.vol, self.ts)

    def local_state(self, state, reason=None):
        with self.lock:
            if state == "PLAYING" and self.state == "PAUSED":
                self.ts = time.time()
            self.state, self.idle_reason = state, reason

    def local_pos(self, t):
        with self.lock:
            self.pos, self.ts = t, time.time()

    def send(self, cmd):
        with self.lock:
            self.cmds.append(cmd)
            if len(self.cmds) > 100:  # janela fechada: não acumula comandos para sempre
                self.cmds = self.cmds[-100:]

    def load(self, url, ctype, title, start):
        with self.lock:
            self.load_id += 1
            self.loaded_ev.clear()
            self.load_err = None
            self.state, self.idle_reason, self.pos, self.dur, self.ts = "BUFFERING", None, float(start), 0.0, time.time()
            self.url = url
            self.cmds = [c for c in self.cmds if c.get("op") not in ("load", "play", "pause", "seek", "stop")]
            self.cmds.append({"op": "load", "id": self.load_id, "url": url, "type": ctype, "title": title,
                              "start": float(start)})
        self.ensure_window()

    def wait_loaded(self, timeout=30):
        if not self.loaded_ev.wait(timeout):
            if not self.alive():
                raise RuntimeError(T("pc_nowin"))
            raise RuntimeError(T("pc_timeout"))
        if self.load_err:
            raise RuntimeError(self.load_err)

    # ----- chamado pelo servidor quando a página envia o relatório -----
    def sync(self, rep):
        """rep: {id, st, t, d, vol, err}. Devolve a lista de comandos pendentes."""
        finished = None
        with self.lock:
            self.last_seen = time.time()
            rid, st = rep.get("id", 0), rep.get("st")
            if rid == self.load_id and rid:
                t, d = float(rep.get("t") or 0), float(rep.get("d") or 0)
                if st in ("playing", "paused", "buffering"):
                    new = {"playing": "PLAYING", "paused": "PAUSED", "buffering": "BUFFERING"}[st]
                    self.state, self.idle_reason = new, None
                    self.pos, self.ts = t, time.time()
                    if d > 0:
                        self.dur = d
                    if st != "buffering" and rid != self.loaded_id:
                        self.loaded_id = rid
                        self.loaded_ev.set()
                elif st == "ended":
                    if self.state != "IDLE":
                        self.state, self.idle_reason, self.pos, self.ts = "IDLE", "FINISHED", t, time.time()
                        finished = MediaStatus(self.state, self.idle_reason, self.pos, self.dur, self.vol, self.ts)
                elif st == "error":
                    self.state, self.idle_reason = "IDLE", "ERROR"
                    self.load_err = str(rep.get("err") or T("pc_err"))[:200]
                    self.loaded_ev.set()
            if rep.get("vol") is not None:
                self.vol = max(0.0, min(1.0, float(rep["vol"])))
            cmds, self.cmds = self.cmds, []
        if finished is not None:
            for l in list(self.listeners):
                try:
                    l.new_media_status(finished)
                except Exception:
                    log(traceback.format_exc())
        return cmds

    # ----- janela -----
    def ensure_window(self):
        if self.alive():
            return
        if self.proc and self.proc.poll() is None and time.time() - getattr(self, "_launched", 0) < 12:
            return  # acabou de abrir, aguardando a página responder
        self.open_window()

    def open_window(self):
        if not self.launch_enabled:
            return
        exe = find_browser()
        if not exe:
            raise RuntimeError(T("pc_nobrowser"))
        os.makedirs(self.profile, exist_ok=True)
        self.close_window()
        args = [exe, "--app=" + self.base_url_fn(), "--user-data-dir=" + self.profile,
                "--autoplay-policy=no-user-gesture-required", "--no-first-run", "--no-default-browser-check",
                "--disable-features=Translate,msEdgeSidebarV2", "--window-size=1000,620"]
        flags = 0
        if sys.platform.startswith("win"):
            flags = 0x08000000  # CREATE_NO_WINDOW (não abre console)
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     creationflags=flags)
        self._launched = time.time()

    def close_window(self):
        p, self.proc = self.proc, None
        if p and p.poll() is None:
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        self.last_seen = 0.0


def find_browser():
    forced = os.environ.get("CP_BROWSER")
    if forced and os.path.isfile(forced):
        return forced
    cands = []
    if sys.platform.startswith("win"):
        for env in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
            base = os.environ.get(env)
            if base:
                cands += [os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"),
                          os.path.join(base, "Google", "Chrome", "Application", "chrome.exe")]
        for p in cands:
            if os.path.isfile(p):
                return p
        return shutil.which("msedge") or shutil.which("chrome")
    for n in ("microsoft-edge", "google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(n)
        if p:
            return p
    return None


PC_HTML = r"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>@@pc_title@@</title><style>
html,body{margin:0;height:100%;background:#000;color:#e9ecf3;font:16px "Segoe UI",system-ui,sans-serif;overflow:hidden}
video{position:absolute;inset:0;width:100%;height:100%;background:#000;object-fit:contain}
#ov{position:absolute;left:0;right:0;top:0;padding:14px 18px;background:linear-gradient(#000a,#0000);
font-weight:600;font-size:18px;pointer-events:none;transition:opacity .4s;text-shadow:0 1px 3px #000}
#msg{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;
padding:24px;color:#8f98ad;pointer-events:none}
</style><video id=v controls autoplay></video><div id=ov></div><div id=msg>@@pc_idle@@</div><script>
const K=new URLSearchParams(location.search).get('k')||'';
const v=document.getElementById('v'),ov=document.getElementById('ov'),msg=document.getElementById('msg');
let id=0,st='idle',err='',startAt=0,ended=false,fade;
function shout(t){ov.textContent=t;ov.style.opacity=1;clearTimeout(fade);fade=setTimeout(()=>ov.style.opacity=0,4000)}
function state(){if(!id)return 'idle';if(err)return 'error';if(ended)return 'ended';
 if(v.paused)return v.readyState<3&&!v.ended&&startAt>=0&&!v.dataset.user?'buffering':'paused';
 return v.readyState<3?'buffering':'playing'}
v.addEventListener('error',()=>{err=(v.error&&v.error.message)||'@@pc_err@@'});
v.addEventListener('ended',()=>{ended=true});
v.addEventListener('pause',()=>{v.dataset.user=v.ended?'':'1'});
v.addEventListener('play',()=>{v.dataset.user=''});
v.addEventListener('loadedmetadata',()=>{if(startAt>0){try{v.currentTime=startAt}catch(e){}}startAt=-1});
function run(c){
 if(c.op=='load'){id=c.id;err='';ended=false;startAt=c.start||0;v.dataset.user='';msg.style.display='none';
  document.title=c.title||'@@pc_title@@';shout(c.title||'');v.src=c.url;v.play().catch(()=>{})}
 else if(c.op=='pause')v.pause();
 else if(c.op=='play'){v.dataset.user='';v.play().catch(()=>{})}
 else if(c.op=='seek')v.currentTime=c.t;
 else if(c.op=='vol')v.volume=c.v;
 else if(c.op=='stop'){v.pause();v.removeAttribute('src');v.load();id=0;msg.style.display='flex';document.title='@@pc_title@@'}}
async function tick(){
 try{const r=await fetch('/pc/sync?k='+K,{method:'POST',body:JSON.stringify({id:id,st:state(),t:v.currentTime||0,
  d:isFinite(v.duration)?v.duration:0,vol:v.volume,err:err})});
  if(r.ok){const j=await r.json();(j.cmds||[]).forEach(run)}}catch(e){}
 setTimeout(tick,400)}
tick();
addEventListener('keydown',e=>{if(e.key=='ArrowRight')v.currentTime+=10;if(e.key=='ArrowLeft')v.currentTime-=10;
 if(e.key==' '){e.preventDefault();v.paused?v.play():v.pause()}if(e.key=='f'||e.key=='F')
 document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen()});
v.addEventListener('dblclick',()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen());
v.addEventListener('mousemove',()=>shout(document.title));
</script>"""


def _page_text(text):
    """Texto traduzido dentro da página (HTML e JavaScript): sem caracteres que quebrem a página."""
    return (str(text).replace("\\", "/").replace("'", "’").replace('"', "”").replace("<", "‹").replace(">", "›")
            .replace("&", "e").replace("\n", " "))


def pc_html():
    import re
    h = PC_HTML
    for k in set(re.findall(r"@@(\w+)@@", h)):
        h = h.replace("@@" + k + "@@", _page_text(T(k)))
    return h
