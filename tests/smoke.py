import os, sys, threading, time
dpi=sys.argv[1]; os.environ["CP_DPI"]=dpi; os.environ["HOME"]=f"{__import__('tempfile').mkdtemp(prefix='tv_')}/h{dpi}"; os.makedirs(os.environ["HOME"],exist_ok=True)
open(os.environ["HOME"]+"/.livingplay.json","w").write('{"terms_ok":1}')
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imageio_ffmpeg; ff=imageio_ffmpeg.get_ffmpeg_exe()
import livingplay as cp
cp.ensure_tools=lambda:(ff,"deno"); cp.update_ytdlp=lambda:True; cp.App.discover=lambda s:None
app=cp.App(); R=[]
T=["Maiara & Maraisa - Medo Bobo (Ao Vivo em Goiânia)","Marília Mendonça - Graveto (Todos Os Cantos - Ao Vivo)"]
app.tracks=[{"title":t,"id":str(i),"url":"u"+str(i)} for i,t in enumerate(T)]
def onmain(fn):
    box={}; ev=threading.Event()
    def run():
        try: box["v"]=fn()
        except Exception as e: box["e"]=e
        ev.set()
    app.after(0,run); ev.wait(10)
    if "e" in box: raise box["e"]
    return box.get("v")
def widgets(w):
    for c in w.winfo_children(): yield c; yield from widgets(c)
def audit(tag):
    def f():
        app.update_idletasks(); W,H=app.winfo_width(),app.winfo_height(); rx,ry=app.winfo_rootx(),app.winfo_rooty(); bad=[]
        for w in widgets(app):
            c=w.winfo_class()
            if c not in ("TButton","TEntry","TCombobox","TSpinbox","Listbox","TRadiobutton") or not w.winfo_viewable() or w.winfo_width()<=1: continue
            p=w; scroll=False
            while p is not None:
                if p.winfo_class()=="Frame" and p.__class__.__name__=="ScrollBox": scroll=True; break
                p=p.master
            if w.winfo_rootx()-rx+w.winfo_width()>W+1 or (not scroll and w.winfo_rooty()-ry+w.winfo_height()>H+1): bad.append(c+":"+str(w.cget("text") if c in("TButton","TRadiobutton") else ""))
            elif c=="TButton" and w.winfo_width()<w.winfo_reqwidth()-3: bad.append("espremido:"+w.cget("text"))
        return W,H,bad
    W,H,bad=onmain(f); R.append(not bad); print(("OK    " if not bad else "FALHOU ")+f"{tag} -> {W}x{H}", bad[:3], flush=True)
def steps():
    time.sleep(2); onmain(lambda:(app.fill_list(),app.refresh_lists()))
    for page in ("play","set","lists","files"):
        onmain(lambda p=page: app.show_page(p)); time.sleep(.6)
        for w,h in ((1000,700),(600,420),(380,260)):
            onmain(lambda w=w,h=h: app.geometry(f"{w}x{h}")); time.sleep(1.0); audit(f"{page} {w}x{h}")
    onmain(lambda: app.show_page("play")); time.sleep(.5)
    from PIL import ImageGrab
    def snap(n):
        app.update_idletasks(); x,y,w,h=app.winfo_rootx(),app.winfo_rooty(),app.winfo_width(),app.winfo_height()
        ImageGrab.grab(xdisplay=os.environ.get("DISPLAY")).crop((x,y,x+w,y+h)).save(f"{os.path.dirname(os.path.abspath(__file__))}/{n}.png")
    onmain(lambda: app.geometry("900x640")); time.sleep(1); snap(f"largo_{dpi}")
    onmain(lambda: app.geometry("520x500")); time.sleep(1.2); snap(f"estreito_{dpi}")
    print("RESULTADO",sum(R),"/",len(R)); app.ui(app.on_close)
threading.Thread(target=steps,daemon=True).start(); app.mainloop()
