import os, sys, threading, time, json, shutil, subprocess, urllib.request, urllib.error
import tempfile; S=tempfile.mkdtemp(prefix="tv_")
H=f"{S}/hf2"; shutil.rmtree(H,ignore_errors=True); os.makedirs(H)
os.environ["HOME"]=H; os.environ["CP_DPI"]="120"
json.dump({"lang":"pt","terms_ok":1,"mode":"video","max_gb":2,"quality":"720"},open(H+"/.livingplay.json","w"))
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imageio_ffmpeg; ff=imageio_ffmpeg.get_ffmpeg_exe()
M=f"{H}/media"; os.makedirs(M)
def mk(name,args):
    subprocess.run([ff,"-y","-loglevel","error","-f","lavfi","-i","testsrc=size=320x180:rate=15:duration=3","-f","lavfi","-i","sine=frequency=440:duration=3"]+args+[f"{M}/{name}"],check=True)
mk("aula um.mp4",["-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-shortest"])
mk("aula dois.mp4",["-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-shortest"])
subprocess.run([ff,"-y","-loglevel","error","-f","lavfi","-i","sine=frequency=330:duration=3",f"{M}/podcast.mp3"],check=True)
import livingplay as cp
from i18n import T
cp.update_ytdlp=lambda:True; cp.App.discover=lambda s:None
_orig=cp.ensure_tools
cp.ensure_tools=lambda:(ff,"deno")
app=cp.App(); RES=[]
def ok(n,c,x=""): RES.append(bool(c)); print(("OK     " if c else "FALHOU ")+n,x,flush=True)
def onmain(fn):
    box={}; ev=threading.Event()
    def run():
        try: box["v"]=fn()
        except Exception: import traceback; box["e"]=traceback.format_exc()
        ev.set()
    app.after(0,run); ev.wait(30)
    if "e" in box: print(box["e"]); RES.append(False)
    return box.get("v")
class Status:
    def __init__(s): s.player_state="IDLE"; s.duration=3; s.adjusted_current_time=0; s.volume_level=0.4
class MC:
    def __init__(s): s.calls=[]; s.status=Status()
    def register_status_listener(s,l): s.l=l
    def play_media(s,url,ctype,**kw): s.calls.append((url,ctype,kw)); s.status.player_state="PLAYING"
    def block_until_active(s,timeout=0): pass
    def pause(s): s.calls.append(("pause",)); s.status.player_state="PAUSED"
    def play(s): s.calls.append(("play",)); s.status.player_state="PLAYING"
    def stop(s): s.calls.append(("stop",)); s.status.player_state="IDLE"
    def seek(s,t): s.calls.append(("seek",t)); s.status.adjusted_current_time=t
class Fake:
    name="Sala"
    class ci: host="192.168.100.19"
    cast_info=ci()
    class sc: is_connected=True
    socket_client=sc()
    def __init__(s): s.media_controller=MC(); s.status=Status(); s.vols=[]
    def wait(s,timeout=0): pass
    def set_volume(s,v): s.vols.append(v)
def get(url,hdr=None):
    r=urllib.request.Request(url,headers=hdr or {})
    try:
        with urllib.request.urlopen(r,timeout=10) as x: return x.status,dict(x.headers),x.read()
    except urllib.error.HTTPError as e: return e.code,dict(e.headers),b""
def steps():
    time.sleep(1.2)
    fk=Fake(); app.devices={"Sala":fk}; onmain(lambda:app.connect("Sala")); time.sleep(1.5)
    ok("conecta e mostra 'Online · Sala'", onmain(lambda:app.pill.text)=="Online · Sala", onmain(lambda:app.pill.text))
    mc=fk.media_controller
    files=[f"{M}/aula um.mp4",f"{M}/aula dois.mp4",f"{M}/podcast.mp3"]
    new=[{"title":os.path.splitext(os.path.basename(p))[0],"path":p} for p in files]
    threading.Thread(target=lambda:app.add_tracks(new,True,name="Cursos"),daemon=True).start()
    for _ in range(80):
        time.sleep(.25)
        if mc.calls: break
    ok("tocar agora: TV recebe o 1º item", len(mc.calls)==1 and mc.calls[0][1].startswith("video"), mc.calls[0][:2] if mc.calls else "")
    url=mc.calls[0][0]
    ok("URL aponta para o servidor local", url.startswith("http://") and "/f/" in url, url)
    st,h,b=get(url); size=len(b)
    ok("servidor entrega o arquivo inteiro (200)", st==200 and size>1000, f"{st} {size}")
    st,h,b2=get(url,{"Range":"bytes=100-199"})
    ok("servidor aceita Range (206, 100 bytes, conteúdo certo)", st==206 and len(b2)==100 and b2==b[100:200] and h.get("Content-Range","").startswith("bytes 100-199/"))
    st,_,_=get(url.rsplit("/f/",1)[0]+"/f/0000/x.mp4"); ok("token inexistente => 404", st==404)
    ok("fila e nome da playlist exibidos", onmain(lambda:(app.lst.size(),app.q_lbl.cget("text")))==(3,"Playlist: Cursos"))
    ok("título e item atual", "Item 1 de 3" in onmain(lambda:app.now_sub.cget("text")), onmain(lambda:app.now_sub.cget("text")))
    # próximo / anterior
    n=len(mc.calls); onmain(app.next_track); time.sleep(2.5)
    ok("próximo toca o 2º item", len(mc.calls)>n and app.idx==1, app.idx)
    n=len(mc.calls); app.pos=0; onmain(app.prev_track); time.sleep(2.5)
    ok("anterior volta ao 1º item", app.idx==0, app.idx)
    n=len(mc.calls); app.idx=2; app.armed=True
    onmain(app.next_track); time.sleep(.8)
    ok("no último item sem repetir: avisa fim e não toca", len(mc.calls)==n and app.last_msg==T("last_item"), app.last_msg)
    onmain(lambda:app.set_repeat(True)); n=len(mc.calls); onmain(app.next_track); time.sleep(2.5)
    ok("com repetir: volta ao início da fila", app.idx==0 and len(mc.calls)>n)
    onmain(lambda:app.set_repeat(False))
    # fim natural do item avança sozinho
    app.armed=True; n=len(mc.calls); app.on_finished(); time.sleep(2.5)
    ok("fim do item avança para o próximo sozinho", app.idx==1 and len(mc.calls)>n)
    # pular 10 s e linha do tempo
    app.dur_now=3; app.pos=1; fk.media_controller.status.adjusted_current_time=1
    onmain(lambda:app.skip(10)); time.sleep(.6)
    ok("pular +10 s é limitado ao fim do item", any(c[0]=="seek" and c[1]<=3 for c in mc.calls if c[0]=="seek"), [c for c in mc.calls if c[0]=="seek"][-1:])
    onmain(lambda:app.seek(1.5)); time.sleep(.5); ok("arrastar a linha do tempo faz seek", mc.calls[-1]==("seek",1.5))
    # volume
    onmain(lambda:app.send_vol(70)); ok("volume vai para a TV", fk.vols and abs(fk.vols[-1]-0.7)<1e-6)
    # aleatório mantém o item atual
    cur=app.tracks[app.idx]["title"]; onmain(lambda:app.set_shuffle(True)); ok("aleatório mantém o item atual no início", app.tracks[0]["title"]==cur and app.idx==0)
    onmain(lambda:app.set_shuffle(False)); ok("desligar aleatório restaura a ordem", [t["title"] for t in app.tracks]==["aula um","aula dois","podcast"])
    # timer "fim do vídeo"
    onmain(lambda:app.set_sleep("end")); app.armed=True; n=len(mc.calls); app.on_finished(); time.sleep(.8)
    ok("timer 'ao fim do vídeo' para em vez de avançar", mc.calls[-1]==("stop",) and not app.stop_after)
    # remoto do celular
    base=f"http://127.0.0.1:{app.remote.port}"; tok=app.token
    st,_,_=get(base+"/?k=errado"); ok("remoto: token errado => 403", st==403)
    st,_,_=get(base+"/"); ok("remoto: sem token => 403", st==403)
    st,h,b=get(base+f"/?k={tok}"); html=b.decode()
    ok("remoto: página em PT com o nome novo", st==200 and "Livingplay" in html and "@@" not in html)
    st,_,b=get(base+f"/api/state?k={tok}"); js=json.loads(b)
    ok("remoto: estado em JSON", js["tracks"]==["aula um","aula dois","podcast"] and "playlists" in js)
    def post(cmd,arg=None):
        r=urllib.request.Request(base+f"/api/cmd?k={tok}",data=json.dumps({"name":cmd,"arg":arg}).encode(),method="POST")
        with urllib.request.urlopen(r,timeout=10) as x: return json.loads(x.read())
    post("shuffle"); ok("remoto: comando aleatório", app.shuffle_on); post("shuffle")
    post("vol",25); ok("remoto: volume", abs(fk.vols[-1]-0.25)<1e-6)
    post("play_idx","xyz"); post("skip","abc"); post("naoexiste"); ok("remoto: comandos inválidos não derrubam o programa", onmain(lambda:True))
    # idioma EN na página remota
    onmain(lambda:(app.var_lang.set("English"),app.change_lang())); time.sleep(1.2)
    st,_,b=get(base+f"/?k={tok}"); ok("remoto: página muda para inglês", "Livingplay" in b.decode() and "Add to queue" in b.decode() and "Sleep timer" in b.decode())
    # persistência: salvar, fechar e abrir de novo
    onmain(lambda:(app.var_theme.set("Light"),app.var_mode.set("audio"),app.var_max.set("5"),app.apply_settings()))
    app.save_session(); time.sleep(.3)
    cfg=json.load(open(cp.CFG))
    ok("arquivo de configuração gravado (idioma, tema, modo, limite, sessão)", cfg.get("lang")=="en" and cfg.get("theme")=="Claro" and cfg.get("mode")=="audio" and cfg.get("max_gb")==5 and cfg["session"]["tracks"], {k:cfg.get(k) for k in ("lang","theme","mode","max_gb")})
    ok("sem arquivo temporário sobrando", not os.path.exists(cp.CFG+".tmp"))
    app.ui(app.on_close); time.sleep(1)
    print("RESULTADO",sum(RES),"/",len(RES)); open(S+"/func2.done","w").write("1")
threading.Thread(target=steps,daemon=True).start(); app.mainloop()
# ---- segunda execução: tudo continua lá?
import importlib
importlib.reload(cp); from i18n import LANG
cp.update_ytdlp=lambda:True; cp.App.discover=lambda s:None; cp.ensure_tools=lambda:(ff,"deno")
app2=cp.App()
r=[LANG["v"]=="en", app2.theme=="Claro", cp.CFGS["mode"]=="audio", cp.CFGS["max_gb"]==5.0, str(cp.CFGS["quality"])=="720", len(app2.cfg["session"]["tracks"])==3]
print(("OK     " if all(r) else "FALHOU ")+"reabrir o programa mantém idioma/tema/modo/limite/qualidade/sessão", r)
app2.destroy()
# arquivo corrompido não apaga em silêncio
open(cp.CFG,"w").write("{quebrado")
d=cp.load_cfg(); print(("OK     " if d=={} and os.path.exists(cp.CFG+".corrompido") else "FALHOU ")+"configuração corrompida vira {} e é guardada em .corrompido")
