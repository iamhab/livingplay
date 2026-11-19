import os, sys, threading, time, json
import tempfile; D=tempfile.mkdtemp(prefix="tv_")
os.environ["CP_DPI"]="120"; os.environ["CP_NO_LAUNCH"]="1"; os.environ["HOME"]=D+"/h11"; os.makedirs(os.environ["HOME"],exist_ok=True)
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
def snap(w,n):
    from PIL import ImageGrab
    def f():
        w.update_idletasks(); return w.winfo_rootx(),w.winfo_rooty(),w.winfo_width(),w.winfo_height()
    x,y,W,H=onmain(f); ImageGrab.grab(xdisplay=os.environ.get("DISPLAY")).crop((x,y,x+W,y+H)).save(f"{D}/{n}.png")
def fits(w):
    def f():
        w.update_idletasks(); bad=[]
        for c in w.winfo_children():
            if c.winfo_ismapped() and (c.winfo_rooty()+c.winfo_height()>w.winfo_rooty()+w.winfo_height()+1 or c.winfo_height()<c.winfo_reqheight()-2): bad.append(str(c))
        return bad
    return onmain(f)
def steps():
    time.sleep(2.5)
    for lang in ("pt","en"):
        if cp.LANG["v"]!=lang: onmain(lambda l=lang: app.apply_language(l)); time.sleep(1.5)
        onmain(app.open_tutorial); time.sleep(.8)
        t=onmain(lambda: app.tut)
        ok(f"{lang}: tutorial abre", t is not None and onmain(t.winfo_exists))
        for i in range(8):
            if i: onmain(lambda: t.go(1)); time.sleep(.3)
            snap(t,f"tut_{lang}_{i+1}")
            bad=fits(t); ok(f"{lang}: passo {i+1} cabe na janela", not bad, bad)
        ok(f"{lang}: último passo mostra Concluir", onmain(lambda: t.b_next.cget("text")) in ("Concluir","Done") if hasattr(t.b_next,"cget") else True)
        onmain(lambda: t.go(1)); time.sleep(.3)
        ok(f"{lang}: Concluir fecha", not onmain(t.winfo_exists))
    # abre duas vezes: não duplica
    onmain(app.open_tutorial); a=onmain(lambda: app.tut); onmain(app.open_tutorial); ok("não abre duas janelas", onmain(lambda: app.tut) is a)
    onmain(lambda: app.apply_language("pt")); time.sleep(1.5)
    ok("trocar idioma fecha o tutorial (sem texto misturado)", onmain(lambda: app.tut) is None)
    print("RESULTADO",sum(R),"/",len(R)); app.ui(app.on_close)
threading.Thread(target=steps,daemon=True).start(); app.mainloop()
