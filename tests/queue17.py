import os, sys, threading, time, json, tempfile
D=tempfile.mkdtemp(prefix="tv_"); os.environ["CP_DPI"]="120"; os.environ["HOME"]=D+"/h"; os.makedirs(os.environ["HOME"],exist_ok=True)
json.dump({"lang":"pt","terms_ok":1,"screen":"aurora"},open(os.environ["HOME"]+"/.livingplay.json","w"))
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imageio_ffmpeg; ff=imageio_ffmpeg.get_ffmpeg_exe()
import livingplay as cp
import dialogs
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
def steps():
    try:
        time.sleep(2)
        ok("config antiga 'aurora' vira Capa", cp.CFGS["screen"]=="cover")
        ok("botão Salvar fila existe", onmain(lambda: app.save_btn.winfo_exists()))
        dialogs.ask_text=lambda *a,**k:"Minha lista"
        app.tracks=[{"url":"https://youtu.be/abcdefghijk","id":"abcdefghijk","title":"A"},{"url":"https://youtu.be/bcdefghijkl","id":"bcdefghijkl","title":"B"}]
        onmain(lambda: app.save_btn.invoke())
        time.sleep(.8)
        ok("playlist salva", len(app.cfg["playlists"].get("Minha lista",[]))==2)
        ok("abriu a aba Playlists", onmain(lambda: app.cur_page)=="lists")
        ok("e selecionou a nova playlist", onmain(lambda: app.sel_pl)=="Minha lista" and onmain(lambda: app.pl_list.curselection())!=())
        ok("itens aparecem à direita", onmain(lambda: app.pl_items.size())==2)
        # fila vazia
        app.tracks=[]; onmain(lambda: app.show_page("play")); onmain(lambda: app.save_btn.invoke()); time.sleep(.3)
        ok("fila vazia não muda de aba", onmain(lambda: app.cur_page)=="play")
        print("RESULTADO",sum(R),"/",len(R))
    finally:
        onmain(lambda: os._exit(0))
threading.Thread(target=steps,daemon=True).start()
app.mainloop()
