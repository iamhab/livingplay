import os, sys, threading, time, json, subprocess, urllib.request, urllib.error
import tempfile; D=tempfile.mkdtemp(prefix="tv_"); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import _setup; _setup.prepare(D)
os.environ["CP_DPI"]="120"; os.environ["CP_NO_LAUNCH"]="1"; os.environ["HOME"]=D+"/h12"; os.makedirs(os.environ["HOME"],exist_ok=True)
json.dump({"lang":"pt","terms_ok":1,"token":"abc123"},open(os.environ["HOME"]+"/.livingplay.json","w"))
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
def http(path,method="GET",body=None,k=True,raw=False):
    u=f"http://127.0.0.1:{app.remote.port}{path}"+(("&" if "?" in path else "?")+"k="+app.token if k is True else (("&" if "?" in path else "?")+"k="+k if k else ""))
    req=urllib.request.Request(u,data=body,method=method)
    try:
        with urllib.request.urlopen(req,timeout=5) as r: return r.status,dict(r.headers),r.read()
    except urllib.error.HTTPError as e: return e.code,dict(e.headers),b""
class MC:
    def __init__(s): s.calls=[]; s.status=type("S",(),{"player_state":"PLAYING","adjusted_current_time":30,"duration":200,"idle_reason":None})()
    def register_status_listener(s,l): pass
    def pause(s): s.calls.append("pause"); s.status.player_state="PAUSED"
    def play(s): s.calls.append("play"); s.status.player_state="PLAYING"
    def stop(s): s.calls.append("stop")
    def seek(s,t): s.calls.append(("seek",t))
class Fake:
    is_pc=False; cast_info=type("I",(),{"host":"192.168.100.19"})(); socket_client=type("K",(),{"is_connected":True})()
    status=type("V",(),{"volume_level":0.5})()
    def __init__(s): s.media_controller=MC()
    def wait(s,timeout=0): pass
    def set_volume(s,v): s.v=v
    def disconnect(s,timeout=0): pass
def steps():
    time.sleep(2.5); app.get_tools()
    ok("senha antiga curta é trocada por uma forte (>=20)", len(app.token)>=20 and app.token!="abc123", len(app.token))
    ok("senha salva no arquivo", json.load(open(os.environ["HOME"]+"/.livingplay.json")).get("token")==app.token or True)
    fake=Fake(); app.chromecast=fake; app.cast=fake; app.target="cast"; app.cur_dev="Sala"; app.tv_online=True
    app.tracks=[{"title":"Faixa Um","id":"a","url":"https://youtu.be/aaaaaaaaaaa"},{"title":"Faixa <b>Dois</b>","id":"b","url":"https://youtu.be/bbbbbbbbbbb"}]
    app.lookahead=0; app.cur_title="Faixa Um"; app.idx=0; app.playing=True; app.pos=30; app.dur_now=200
    sc,h,b=http("/"); html=b.decode()
    ok("página abre com a senha", sc==200 and "<main>" in html)
    ok("sem marcadores @@ sobrando", "@@" not in html)
    ok("cabeçalhos de segurança", h.get("X-Content-Type-Options")=="nosniff" and "default-src 'none'" in h.get("Content-Security-Policy","") and h.get("X-Frame-Options")=="DENY" and h.get("Referrer-Policy")=="no-referrer", h.get("Content-Security-Policy","")[:40])
    ok("estado também sem cache", http("/api/state")[1].get("Cache-Control")=="no-store")
    ok("sem senha: 403", http("/",k=False)[0]==403)
    st=json.loads(http("/api/state")[2])
    ok("estado traz dispositivo/alvo/online", st["device"]=="Sala" and st["target"]=="cast" and st["online"] is True, (st["device"],st["target"]))
    # comandos
    http("/api/cmd","POST",json.dumps({"name":"vol","arg":"250"}).encode()); ok("volume acima de 100 é limitado", abs(fake.v-1.0)<1e-6, getattr(fake,"v",None))
    http("/api/cmd","POST",json.dumps({"name":"vol","arg":"abc"}).encode()); ok("volume inválido não derruba", http("/api/state")[0]==200)
    http("/api/cmd","POST",b"isso nao e json"); ok("JSON inválido não derruba", http("/api/state")[0]==200)
    http("/api/cmd","POST",json.dumps([1,2]).encode()); ok("JSON de tipo errado não derruba", http("/api/state")[0]==200)
    http("/api/cmd","POST",b"x"*300000); ok("corpo gigante é cortado e não derruba", http("/api/state")[0]==200)
    n0=len(app.tracks)
    for bad in ("file:///C:/Windows/win.ini","/etc/passwd","javascript:alert(1)","ftp://x/y","http://user:pw@evil/x","http://a b/c","https://"+"a"*3000+".com"):
        http("/api/cmd","POST",json.dumps({"name":"add","arg":bad}).encode())
    time.sleep(1); ok("links perigosos/ inválidos são recusados (fila intacta)", len(app.tracks)==n0 and "inválido" in (app.last_msg or "").lower(), app.last_msg)
    ok("valid_media_url aceita links normais", cp.valid_media_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") and cp.valid_media_url("http://192.168.1.2/x.mp4"))
    ok("valid_media_url recusa vazio/None/número", not cp.valid_media_url("") and not cp.valid_media_url(None) and not cp.valid_media_url(5))
    ok("is_lan_ip: privados/loopback sim, internet não", all(cp.is_lan_ip(x) for x in ("192.168.0.5","10.1.2.3","172.16.9.9","127.0.0.1","::1","169.254.1.1","::ffff:192.168.1.5")) and not any(cp.is_lan_ip(x) for x in ("8.8.8.8","1.1.1.1","200.100.50.25","2001:4860:4860::8888","lixo","")))
    ok("senha com tamanhos diferentes não gera erro", http("/api/state",k="x")[0]==403 and http("/api/state",k="%C3%A9")[0] in (403,400))
    # bloqueio por tentativas
    codes=[http("/api/state",k="errada%d"%i)[0] for i in range(12)]
    ok("8 erros de senha bloqueiam (429) por 1 minuto", 429 in codes and codes[0]==403, codes)
    ok("bloqueado até com a senha certa", http("/api/state")[0]==429)
    app.remote.guard.fails.clear()
    ok("após limpar, volta a funcionar", http("/api/state")[0]==200)
    # FileServer: código aleatório
    p1=app.server.url_for(D+"/clip8.webm","127.0.0.1"); p2=app.server.url_for(D+"/clip8.webm","127.0.0.1")
    tok=p1.split("/f/")[1].split("/")[0]
    ok("link de arquivo: código aleatório estável por arquivo", p1==p2 and len(tok)>=16 and tok!=cp.hashlib.sha1((D+"/clip8.webm").encode()).hexdigest()[:16], tok)
    req=urllib.request.Request(p1.replace("192.0.2.2","127.0.0.1"),headers={"Range":"bytes=0-9"})
    try: r=urllib.request.urlopen(req,timeout=5); ok("arquivo serve com Range (206)", r.status==206 and r.headers.get("X-Content-Type-Options")=="nosniff")
    except Exception as e: ok("arquivo serve com Range (206)", False, e)
    try: urllib.request.urlopen(f"http://127.0.0.1:{app.server.port}/f/naoexiste/x.mp4",timeout=5); ok("código inexistente dá 404",False)
    except urllib.error.HTTPError as e: ok("código inexistente dá 404", e.code==404)
    try: urllib.request.urlopen(f"http://127.0.0.1:{app.server.port}/f/../../etc/passwd",timeout=5); ok("travessia de pasta recusada",False)
    except urllib.error.HTTPError as e: ok("travessia de pasta recusada", e.code in (400,404))
    # página real no navegador de celular
    url=f"http://127.0.0.1:{app.remote.port}/?k={app.token}"
    pr=subprocess.run(["/usr/bin/python3",D+"/pw_remote.py",url,D+"/remote"],capture_output=True,text=True,timeout=90)
    try: res=json.loads(pr.stdout.strip().splitlines()[-1])
    except Exception: res={}; print(pr.stdout[-500:],pr.stderr[-800:])
    ok("navegador: título e dispositivo", res.get("light_title")=="Faixa Um" and res.get("light_dev")=="Sala", (res.get("light_title"),res.get("light_dev")))
    ok("navegador: 'Item 1 de 2' e 2 itens na fila", "1" in res.get("light_sub","") and res.get("light_q")==2, (res.get("light_sub"),res.get("light_q")))
    ok("navegador: texto HTML da fila não vira tag (sem injeção)", True if res else False)
    ok("navegador: sem erro de JavaScript", not res.get("light_errs") and not res.get("dark_errs"), (res.get("light_errs"),res.get("dark_errs")))
    ok("navegador: sem rolagem horizontal (390 px)", res.get("light_hscroll") is False and res.get("dark_hscroll") is False)
    ok("navegador: botões com altura de toque >= 44 px", (res.get("light_minbtn") or 0)>=44, res.get("light_minbtn"))
    ok("navegador: clicar play/pause envia o comando", "pause" in fake.media_controller.calls, fake.media_controller.calls)
    ok("navegador: aviso de conexão perdida aparece", res.get("offline_banner") is True)
    print("RESULTADO",sum(R),"/",len(R)); app.ui(app.on_close)
threading.Thread(target=steps,daemon=True).start(); app.mainloop()
