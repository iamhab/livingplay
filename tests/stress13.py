import os, sys, threading, time, json, urllib.request
import tempfile; D=tempfile.mkdtemp(prefix="tv_")
os.environ["CP_DPI"]="120"; os.environ["CP_NO_LAUNCH"]="1"; os.environ["HOME"]=D+"/h13"; os.makedirs(os.environ["HOME"],exist_ok=True)
json.dump({"lang":"pt","terms_ok":1},open(os.environ["HOME"]+"/.livingplay.json","w"))
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imageio_ffmpeg; ff=imageio_ffmpeg.get_ffmpeg_exe()
import livingplay as cp
cp.ensure_tools=lambda:(ff,"deno"); cp.update_ytdlp=lambda force=False:True; cp.App.discover=lambda s:None
app=cp.App(); R=[]
def onmain(fn):
    box={}; ev=threading.Event()
    def run():
        try: box["v"]=fn()
        except Exception as e: box["e"]=e
        ev.set()
    app.after(0,run); ev.wait(20)
    if "e" in box: raise box["e"]
    return box.get("v")
def ok(n,c,x=""): R.append(bool(c)); print(("OK     " if c else "FALHOU ")+n,x,flush=True)
def rss(): return int([l for l in open("/proc/self/status") if l.startswith("VmRSS")][0].split()[1])//1024
def fds(): return len(os.listdir("/proc/self/fd"))
def snapm(): return threading.active_count(), fds(), rss()
class MC:
    def __init__(s): s.status=type("S",(),{"player_state":"PLAYING","adjusted_current_time":30,"duration":200,"idle_reason":None})()
    def register_status_listener(s,l): pass
    def pause(s): pass
    def play(s): pass
    def stop(s): pass
    def seek(s,t): pass
class Fake:
    is_pc=False; cast_info=type("I",(),{"host":"192.168.100.19"})(); socket_client=type("K",(),{"is_connected":True})()
    status=type("V",(),{"volume_level":0.5})()
    def __init__(s): s.media_controller=MC()
    def wait(s,timeout=0): pass
    def set_volume(s,v): pass
    def disconnect(s,timeout=0): pass
def steps():
    time.sleep(3); app.get_tools(); app.lookahead=0
    fake=Fake(); app.chromecast=fake; app.cast=fake; app.target="cast"; app.cur_dev="Sala"; app.tv_online=True
    app.tracks=[{"title":f"Faixa {i}","id":str(i),"url":"u"} for i in range(50)]
    app.cur_title="Faixa 0"; app.playing=True
    pc=app.get_pcdev()
    port=app.remote.port; base=f"http://127.0.0.1:{port}"
    def get(p):
        with urllib.request.urlopen(f"{base}{p}{'&' if '?' in p else '?'}k={app.token}",timeout=5) as r: return r.read()
    for _ in range(50): get("/api/state")  # aquece
    time.sleep(2); a=snapm(); print("início  threads/fds/MB:",a,flush=True)
    stop=[False]; errs=[0]; cnt=[0]
    def hammer():
        while not stop[0]:
            try:
                get("/api/state"); cnt[0]+=1
                req=urllib.request.Request(f"{base}/pc/sync?k={app.token}",data=json.dumps({"id":0,"st":"idle","t":0,"d":0,"vol":1}).encode(),method="POST"); urllib.request.urlopen(req,timeout=5).read()
            except Exception: errs[0]+=1
    ths=[threading.Thread(target=hammer,daemon=True) for _ in range(6)]
    for t in ths: t.start()
    for i in range(24):
        onmain(lambda i=i: app.apply_language("en" if i%2==0 else "pt")); time.sleep(.7)
        if i%6==0: onmain(lambda: (app.var_theme.set(cp.T("th_Escuro" if app.theme=="Claro" else "th_Claro")),app.apply_settings())); time.sleep(.8)
    time.sleep(2); stop[0]=True; time.sleep(1.5)
    b=snapm(); print("fim     threads/fds/MB:",b,f" requisições={cnt[0]} erros={errs[0]}",flush=True)
    ok("sem erros nas requisições sob carga", errs[0]==0, errs[0])
    ok("threads não crescem (<= +6)", b[0]-a[0]<=6, (a[0],b[0]))
    ok("descritores de arquivo não vazam (<= +10)", b[1]-a[1]<=10, (a[1],b[1]))
    ok("memória estável (<= +60 MB após 24 reconstruções)", b[2]-a[2]<=60, (a[2],b[2]))
    ok("interface ainda responde", onmain(lambda: app.winfo_exists())==1)
    # encerramento limpo
    th0=threading.active_count()
    app.ui(app.on_close); time.sleep(2)
    print("RESULTADO",sum(R),"/",len(R),flush=True)
threading.Thread(target=steps,daemon=True).start(); app.mainloop()
