import os, sys, threading, time, json, tempfile
D=tempfile.mkdtemp(prefix="tv_"); os.environ["CP_DPI"]="120"; os.environ["HOME"]=D+"/h"; os.makedirs(os.environ["HOME"],exist_ok=True)
json.dump({"lang":"pt","terms_ok":1,"max_gb":1.0},open(os.environ["HOME"]+"/.livingplay.json","w"))
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
    app.after(0,run); ev.wait(20)
    if "e" in box: raise box["e"]
    return box.get("v")
def ok(n,c,x=""): R.append(bool(c)); print(("OK     " if c else "FALHOU ")+n,x,flush=True)
GB=1024**3
def fake(pct):
    cp.cache_inventory=lambda: {"videos":[("/x/a.mp4",int(GB*pct/100)+4096,0)],"temp":[]}
def check(pct):
    fake(pct); onmain(lambda: app.refresh_usage()); time.sleep(.8)
def steps():
    try:
        time.sleep(2.5)
        check(30); ok("30%: indicador escondido", not onmain(lambda: app.space_btn.winfo_ismapped()))
        check(55); ok("55%: indicador 'Pasta 55%' aparece", onmain(lambda: app.space_btn.winfo_ismapped()) and "55%" in app.space_btn.cget("text"), app.space_btn.cget("text"))
        ok("55%: aviso enviado", "55%" in app.last_msg, app.last_msg[:60])
        app.last_msg=""; check(60); ok("60%: não repete o aviso do mesmo nível", app.last_msg=="")
        check(80); ok("80%: novo aviso", "80%" in app.last_msg, app.last_msg[:50])
        check(95); ok("95%: aviso 'quase cheia'", "quase cheia" in app.last_msg)
        check(100); ok("100%: aviso de limite", "limite" in app.last_msg and "apagados" in app.last_msg)
        ok("texto em Ajustes mostra a porcentagem", "100%" in onmain(lambda: app.usage_lbl.cget("text")))
        app.last_msg=""; check(20); ok("volta a esconder quando esvazia", not onmain(lambda: app.space_btn.winfo_ismapped()))
        check(55); ok("e avisa de novo ao subir outra vez", "55%" in app.last_msg)
        onmain(lambda: app.space_btn.invoke()); time.sleep(.3)
        ok("clicar no indicador abre Ajustes", onmain(lambda: app.cur_page)=="set")
        cp.CFGS["max_gb"]=0; check(90); ok("sem limite: sem indicador", not onmain(lambda: app.space_btn.winfo_ismapped()) and "Sem limite" in onmain(lambda: app.usage_lbl.cget("text")))
        vd=os.path.join(cp.CFGS["cache"],"visuals"); os.makedirs(vd,exist_ok=True)
        for n in ("a"*16,"b"*16,"c"*16): open(f"{vd}/{n}.mp4","wb").write(b"x")
        cp.trim_visuals(f"{vd}/{'b'*16}.mp4")
        ok("telas temporárias: só a atual fica", os.listdir(vd)==["b"*16+".mp4"])
        print("RESULTADO",sum(R),"/",len(R))
    finally:
        onmain(lambda: os._exit(0))
threading.Thread(target=steps,daemon=True).start()
app.mainloop()
