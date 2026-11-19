import os, sys, threading, time, json
import tempfile; D=tempfile.mkdtemp(prefix="tv_")
os.environ["CP_DPI"]="120"; os.environ["HOME"]=D+"/h9"; os.makedirs(os.environ["HOME"],exist_ok=True)
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
def snap(n):
    from PIL import ImageGrab
    def f():
        app.update_idletasks(); return app.winfo_rootx(),app.winfo_rooty(),app.winfo_width(),app.winfo_height()
    x,y,w,h=onmain(f); ImageGrab.grab(xdisplay=os.environ.get("DISPLAY")).crop((x,y,x+w,y+h)).save(f"{D}/{n}.png")
def click(widget):
    def f():
        widget.event_generate("<Button-1>",x=widget.winfo_width()-6,y=widget.winfo_height()//2)
        widget.event_generate("<ButtonRelease-1>",x=widget.winfo_width()-6,y=widget.winfo_height()//2)
    onmain(f)
def steps():
    time.sleep(2)
    onmain(lambda: app.geometry("900x700")); time.sleep(.8)
    ok("tema padrão é Claro", onmain(lambda: app.theme)=="Claro")
    ok("idioma inicial PT", onmain(lambda: cp.LANG["v"])=="pt" and "Reproduzir" in onmain(lambda: app.target_sw.__class__.__name__ and "Reproduzir em"))
    click(app.lang_sw); time.sleep(1.5)
    ok("clique no interruptor troca para EN na hora", onmain(lambda: cp.LANG["v"])=="en", onmain(lambda: cp.LANG["v"]))
    ok("idioma EN salvo no arquivo", json.load(open(os.environ["HOME"]+"/.livingplay.json")).get("lang")=="en")
    snap("p9_en"); click(app.lang_sw); time.sleep(1.5)
    ok("clique de novo volta para PT", onmain(lambda: cp.LANG["v"])=="pt")
    time.sleep(1.0)
    def texts():
        out=[]
        def walk(w):
            for c in w.winfo_children():
                try: out.append(c.cget("text"))
                except Exception: pass
                walk(c)
        walk(app); return [t for t in out if isinstance(t,str)]
    tx=" | ".join(onmain(texts))
    ok("sem inglês misturado no PT", not any(w in tx for w in ("Play now","Queue","Settings","Find TV","Phone remote")), [w for w in ("Play now","Queue","Settings","Find TV","Phone remote") if w in tx])
    onmain(lambda: app.show_page("set")); time.sleep(.8); snap("p9_set_pt")
    # lista de dispositivos
    class C: pass
    onmain(lambda: (app.devices.update({"Sala":object(),"Quarto":object()}), app.fill_devices()))
    ok("lista mostra 2 TVs", onmain(lambda: app.dev_list.size())==2)
    ok("combo da barra tem as 2 TVs", set(onmain(lambda: app.combo["values"]))=={"Sala","Quarto"})
    # alternância de alvo persiste
    onmain(lambda: app.on_target("pc")); time.sleep(2.5); ok("alvo 'pc' salvo", json.load(open(os.environ["HOME"]+"/.livingplay.json")).get("target")=="pc")
    onmain(lambda: app.on_target("cast")); time.sleep(1.5)
    # tema escuro
    onmain(lambda: (app.var_theme.set(cp.T("th_Escuro")),app.apply_settings())); time.sleep(1.5)
    ok("tema escuro aplicado na hora", onmain(lambda: app.theme)=="Escuro")
    onmain(lambda: app.show_page("play")); time.sleep(.6); snap("p9_dark")
    # limite de reconexão
    app.cast=type("X",(),{"cast_info":type("I",(),{"host":"1.2.3.4"})(),"disconnect":lambda s,timeout=0:None})()
    calls=[]; app.bg=lambda fn: calls.append(1)
    def sim():
        t=time.time()
        for i in range(40):
            app.watch_connection(False); app.next_retry=0 if app.retry_n<5 else app.next_retry; 
        return app.retry_n
    n=onmain(sim); ok("reconexão limitada a 5 tentativas", n==5 and len(calls)==5, (n,len(calls)))
    onmain(lambda: app.watch_connection(True)); ok("voltar Online zera as tentativas", onmain(lambda: app.retry_n)==0)
    print("RESULTADO",sum(R),"/",len(R)); app.ui(app.on_close)
threading.Thread(target=steps,daemon=True).start(); app.mainloop()
