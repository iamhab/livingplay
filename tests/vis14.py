import os, sys, threading, time, json, re
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
import subprocess, shutil
def probe(p):
    r=subprocess.run([ff,"-hide_banner","-i",p],capture_output=True,text=True).stderr
    return r
def steps():
    try:
        time.sleep(1.5)
        src=D+"/musica.mp3"
        subprocess.run([ff,"-y","-loglevel","error","-f","lavfi","-i","sine=f=440:d=6,tremolo=f=3:d=.9","-metadata","title=Faixa de Teste","-metadata","artist=Artista Exemplo","-c:a","libmp3lame",src],check=True)
        app.tools=(ff,"deno")
        info={"path":src,"title":"musica","ctype":"audio/mpeg","local":True}
        for style in ("cover",):
            cp.CFGS["screen"]=style
            out=onmain(lambda: app.visual_for(info))
            ok(f"{style}: arquivo gerado", bool(out) and os.path.isfile(out), out)
            pr=probe(out) if out else ""
            ok(f"{style}: tem vídeo H.264 e áudio", "Video: h264" in pr and "Audio:" in pr)
            ok(f"{style}: duração ~6 s", "Duration: 00:00:06" in pr or "Duration: 00:00:05" in pr, re.search(r"Duration: [\d:.]+",pr).group(0) if "Duration" in pr else "")
            t0=time.time(); out2=onmain(lambda: app.visual_for(info)); ok(f"{style}: segunda vez usa o arquivo pronto", out2==out and time.time()-t0<1)
            ok(f"{style}: dentro da pasta visuals do cache", os.path.basename(os.path.dirname(out))=="visuals")
        inv=cp.cache_inventory()
        ok("inventário enxerga as telas geradas", sum(1 for x in inv["videos"] if os.sep+"visuals"+os.sep in x[0])==1, len(inv["videos"]))
        ok("sem sobras .part/.png", not [x for x in inv["temp"] if os.sep+"visuals"+os.sep in x[0]])
        # falha controlada: áudio inexistente não derruba o programa
        bad={"path":D+"/nao_existe.mp3","title":"x","ctype":"audio/mpeg","local":True}
        ok("arquivo inválido devolve None sem erro", onmain(lambda: app.visual_for(bad)) is None)
        # apagar tudo apaga as telas também
        vids=[x for x in cp.cache_inventory()["videos"]]
        cp.delete_files(vids)
        ok("limpeza remove as telas", not os.listdir(os.path.join(cp.CFGS["cache"],"visuals")))
        # ---- ponta a ponta: tocar um MP3 local na "TV" (falsa) e conferir o que foi enviado
        import urllib.request
        class MC:
            status=None; calls=[]
            def register_status_listener(self,l): pass
            def stop(self): pass
            def play_media(self,url,ctype,**kw): MC.calls.append((url,ctype,kw))
            def block_until_active(self,timeout=0): pass
        class Fake:
            name=None
            def __init__(s): s.media_controller=MC(); s.status=None; s.connected=True
            class ci: host="127.0.0.1"
            cast_info=ci()
            class sc: is_connected=True
            socket_client=sc()
            def wait(self,timeout=0): pass
            def set_volume(self,v): pass
        for style in ("cover",):
            cp.CFGS["screen"]=style; MC.calls.clear()
            app.cast=Fake(); app.server=cp.FileServer(); app.tools=(ff,"deno")
            app.tracks=[{"path":src,"title":"musica"}]; app.idx=0
            onmain(lambda: app.bg(lambda: app.play_index(0)))
            for _ in range(60):
                if MC.calls: break
                time.sleep(.5)
            ok(f"{style}: a TV recebeu um pedido de reprodução", len(MC.calls)==1)
            url,ct,kw=MC.calls[0] if MC.calls else ("","",{})
            ok(f"{style}: enviado como vídeo mp4 (tela cheia do programa)", ct=="video/mp4" and url.endswith(".mp4"), ct)
            try:
                r=urllib.request.urlopen(urllib.request.Request(url.replace(url.split("/")[2],"127.0.0.1:"+url.split(":")[2].split("/")[0]),headers={"Range":"bytes=0-99"}))
                ok(f"{style}: servidor entrega o vídeo (206)", r.status==206 and len(r.read())==100)
            except Exception as e:
                ok(f"{style}: servidor entrega o vídeo (206)", False, e)
        print("RESULTADO", sum(R), "/", len(R), flush=True)
    finally:
        onmain(lambda: os._exit(0))
threading.Thread(target=steps,daemon=True).start()
app.mainloop()
