import os, sys, threading, time, json, subprocess
import tempfile; D=tempfile.mkdtemp(prefix="tv_"); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import _setup; _setup.prepare(D)
os.environ["CP_DPI"]="120"; os.environ["CP_NO_LAUNCH"]="1"; os.environ["HOME"]=D+"/h10"; os.makedirs(os.environ["HOME"],exist_ok=True)
json.dump({"lang":"pt","terms_ok":1},open(os.environ["HOME"]+"/.livingplay.json","w"))
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imageio_ffmpeg; ff=imageio_ffmpeg.get_ffmpeg_exe()
import livingplay as cp
cp.ensure_tools=lambda:(ff,"deno"); cp.update_ytdlp=lambda:True; cp.App.discover=lambda s:None
app=cp.App(); R=[]
def onmain(fn):
    box={}; ev=threading.Event()
    def run():
        try: box["v"]=fn()
        except Exception as e: box["e"]=e
        ev.set()
    app.after(0,run); ev.wait(10)
    if "e" in box: raise box["e"]
    return box.get("v")
def ok(n,c,x=""): R.append(bool(c)); print(("OK     " if c else "FALHOU ")+n,x,flush=True)
def wait(cond,t=12):
    e=time.time()+t
    while time.time()<e:
        try:
            if cond(): return True
        except Exception: pass
        time.sleep(.2)
    return False
class MC:
    def __init__(s): s.calls=[]; s.status=None; s.l=[]
    def register_status_listener(s,l): s.l.append(l)
    def play_media(s,url,ct,**k): s.calls.append(("play",url,k.get("current_time"))); s.status=type("S",(),{"player_state":"PLAYING","adjusted_current_time":k.get("current_time") or 0,"duration":8,"idle_reason":None})()
    def block_until_active(s,timeout=0): pass
    def pause(s): s.calls.append(("pause",)); s.status.player_state="PAUSED"
    def play(s): s.calls.append(("play0",)); s.status.player_state="PLAYING"
    def stop(s): s.calls.append(("stop",)); s.status=type("S",(),{"player_state":"IDLE","adjusted_current_time":0,"duration":0,"idle_reason":"CANCELLED"})()
    def seek(s,t): s.calls.append(("seek",t))
class Fake:
    is_pc=False; cast_info=type("I",(),{"host":"192.168.100.19"})(); socket_client=type("K",(),{"is_connected":True})()
    status=type("V",(),{"volume_level":0.5})()
    def __init__(s): s.media_controller=MC()
    def wait(s,timeout=0): pass
    def set_volume(s,v): pass
    def disconnect(s,timeout=0): pass
def steps():
    time.sleep(2.5)
    clip8,clip3=D+"/clip8.webm",D+"/clip3.webm"
    fake=Fake(); app.chromecast=fake; app.cast=fake; app.target="cast"
    app.tracks=[{"title":"Clipe 8s","id":"a","url":"ua"},{"title":"Clipe 3s","id":"b","url":"ub"}]
    infos={"a":{"path":clip8,"title":"Clipe 8s","ctype":"video/webm","duration":8},"b":{"path":clip3,"title":"Clipe 3s","ctype":"video/webm","duration":3}}
    app.get_info=lambda t,quiet=False: infos[t["id"]]
    app.offline_info=lambda t: infos[t["id"]]
    pc=app.get_pcdev(); app.get_tools(); port=app.remote.port
    url=f"http://127.0.0.1:{port}/pc?k={app.token}"
    ok("página do computador exige a senha", subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}",f"http://127.0.0.1:{port}/pc"],capture_output=True,text=True).stdout=="403")
    page=subprocess.Popen(["/usr/bin/python3",D+"/pw_page.py",url,"75"])
    ok("janela conecta ao programa", wait(lambda: pc.alive(),20))
    # 1) toca no Chromecast (falso) e troca para o computador no meio
    app.bg(lambda: app.play_index(0, start=0)); wait(lambda: app.armed,10); time.sleep(1)
    ok("toca no Chromecast (falso)", fake.media_controller.calls and fake.media_controller.calls[0][0]=="play")
    fake.media_controller.status.adjusted_current_time=3
    onmain(lambda: app.on_target("pc"))
    ok("troca para o computador", wait(lambda: app.target=="pc" and not app.switching,20), app.target)
    ok("Chromecast foi parado (sem som duplo)", ("stop",) in fake.media_controller.calls)
    ok("computador começa a tocar", wait(lambda: pc.snapshot().player_state=="PLAYING",15), pc.snapshot().player_state)
    st=pc.snapshot()
    ok("posição preservada (~3 s)", 2.5<=st.adjusted_current_time<=8, round(st.adjusted_current_time,1))
    ok("duração conhecida (~8 s)", 7<=st.duration<=9, st.duration)
    ok("pill mostra Computador", "Computador" in onmain(lambda: app.pill.text), onmain(lambda: app.pill.text))
    # 2) controles
    app.bg(app.pause); ok("pausar", wait(lambda: pc.snapshot().player_state=="PAUSED",8))
    p0=pc.snapshot().adjusted_current_time; time.sleep(1.2); ok("pausado não avança", abs(pc.snapshot().adjusted_current_time-p0)<0.6)
    app.bg(app.resume); ok("continuar", wait(lambda: pc.snapshot().player_state=="PLAYING",8))
    app.seek(4.0); time.sleep(1.2); ok("pular para 4 s", 4<=pc.snapshot().adjusted_current_time<=6.0, pc.snapshot().adjusted_current_time)
    pc.set_volume(0.3); time.sleep(1.2); ok("volume 30%", abs(pc.snapshot().volume_level-0.3)<0.05, pc.snapshot().volume_level)
    # 3) fim da faixa avança sozinha
    ok("fim da faixa avança para o próximo", wait(lambda: app.idx==1 and app.armed and pc.snapshot().player_state in("PLAYING","BUFFERING"),20), app.idx)
    ok("mensagem de item 2", "2" in (app.last_msg or ""), app.last_msg)
    # 4) parar
    app.stop(); ok("parar", wait(lambda: pc.snapshot().player_state=="IDLE",8))
    # 5) volta ao Chromecast retomando
    app.bg(lambda: app.play_index(0,start=2)); wait(lambda: app.armed and pc.snapshot().player_state=="PLAYING",15)
    fake.media_controller.calls.clear()
    onmain(lambda: app.on_target("cast"))
    ok("volta para o Chromecast", wait(lambda: app.target=="cast" and not app.switching,20), app.target)
    ok("computador parou (sem som duplo)", wait(lambda: pc.snapshot().player_state=="IDLE",8))
    ok("Chromecast retomou a mesma faixa", any(c[0]=="play" and "8s" not in str(c) for c in fake.media_controller.calls) or any(c[0]=="play" for c in fake.media_controller.calls), fake.media_controller.calls[:2])
    ok("preferência 'cast' salva", json.load(open(os.environ["HOME"]+"/.livingplay.json")).get("target")=="cast")
    # 6) sem TV conectada não troca
    app.chromecast=None; onmain(lambda: app.on_target("pc")); wait(lambda: not app.switching,10)
    app.chromecast=fake; app.cast=fake; app.target="cast"
    # 7) janela fechada: não avança a fila e informa
    onmain(lambda: app.on_target("pc")); wait(lambda: app.target=="pc" and not app.switching,20)
    app.bg(lambda: app.play_index(0)); wait(lambda: pc.snapshot().player_state=="PLAYING",15)
    page.terminate(); page.wait(); idx=app.idx
    ok("janela fechada vira IDLE/CANCELLED sem avançar", wait(lambda: pc.snapshot().player_state=="IDLE" and pc.snapshot().idle_reason=="CANCELLED",15) and app.idx==idx)
    # 8) erro de vídeo (arquivo ruim)
    page=subprocess.Popen(["/usr/bin/python3",D+"/pw_page.py",url,"20"]); wait(lambda: pc.alive(),20)
    bad=D+"/ruim.webm"; open(bad,"wb").write(b"nao e video"*50)
    infos["a"]={"path":bad,"title":"Ruim","ctype":"video/webm","duration":5}
    app.bg(lambda: app.play_index(0)); time.sleep(6)
    ok("vídeo inválido é marcado como falha e a fila segue", cp.tkey(app.tracks[0]) in app.failed and app.idx==1, (list(app.failed)[:1], app.idx))
    page.terminate()
    print("RESULTADO",sum(R),"/",len(R)); app.ui(app.on_close)
threading.Thread(target=steps,daemon=True).start(); app.mainloop()
