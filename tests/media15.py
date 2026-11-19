import os, sys, threading, time, json, re, subprocess
import tempfile; D=tempfile.mkdtemp(prefix="tv_")
os.environ["CP_DPI"]="120"; os.environ["HOME"]=D+"/h9"; os.makedirs(os.environ["HOME"],exist_ok=True)
json.dump({"lang":"pt","terms_ok":1},open(os.environ["HOME"]+"/.livingplay.json","w"))
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imageio_ffmpeg; ff=imageio_ffmpeg.get_ffmpeg_exe()
import livingplay as cp, mediatools as mt
cp.ensure_tools=lambda:(ff,"deno"); cp.update_ytdlp=lambda:True; cp.App.discover=lambda s:None
app=cp.App(); R=[]
def onmain(fn):
    box={}; ev=threading.Event()
    def run():
        try: box["v"]=fn()
        except Exception as e: box["e"]=e
        ev.set()
    app.after(0,run); ev.wait(60)
    if "e" in box: raise box["e"]
    return box.get("v")
def ok(n,c,x=""): R.append(bool(c)); print(("OK     " if c else "FALHOU ")+n,x,flush=True)
def sh(*a): return subprocess.run([ff,"-nostdin","-loglevel","error","-y",*a],capture_output=True,text=True)
def loud(p):
    e=subprocess.run([ff,"-nostdin","-i",p,"-af","ebur128","-f","null","-"],capture_output=True,text=True).stderr
    m=re.findall(r"I:\s+(-?[\d.]+) LUFS",e); return float(m[-1]) if m else None
def steps():
    try:
        time.sleep(1.5)
        W=D+"/w"; os.makedirs(W); cache=cp.CFGS["cache"]
        # ---- SRT -> VTT
        v=mt.srt_to_vtt("1\r\n00:00:01,500 --> 00:00:03,000\r\n<font color=red>Olá</font> {\\an8}mundo\r\n")
        ok("srt vira vtt", v.startswith("WEBVTT") and "00:00:01.500 --> 00:00:03.000" in v and "<font" not in v and "\\an8" not in v, repr(v[:60]))
        # ---- legenda ao lado do vídeo (cp1252) e escolha de idioma
        sh("-f","lavfi","-i","color=c=blue:s=320x240:d=3","-f","lavfi","-i","sine=f=440:d=3","-shortest","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac",W+"/filme.mp4")
        open(W+"/filme.pt.srt","wb").write("1\n00:00:00,500 --> 00:00:02,000\nAção e emoção\n".encode("cp1252"))
        open(W+"/filme.en.srt","w").write("1\n00:00:00,500 --> 00:00:02,000\nAction\n")
        a=mt.local_vtt(W+"/filme.mp4","pt",cache,ff); b=mt.local_vtt(W+"/filme.mp4","en",cache,ff)
        ok("legenda pt escolhida e acentos corretos", a and "Ação e emoção" in open(a,encoding="utf-8").read())
        ok("legenda en escolhida", b and "Action" in open(b,encoding="utf-8").read())
        ok("sem legenda -> None", mt.local_vtt(W+"/filme.mp4","pt",cache,ff) is not None and mt.local_vtt(W+"/nao.mp4","pt",cache,ff) is None)
        # ---- legenda embutida (mkv)
        open(W+"/emb.srt","w").write("1\n00:00:00,200 --> 00:00:01,500\nDentro do arquivo\n")
        r=sh("-i",W+"/filme.mp4","-i",W+"/emb.srt","-map","0","-map","1","-c","copy","-c:s","srt","-metadata:s:s:0","language=por",W+"/emb.mkv")
        c=mt.local_vtt(W+"/emb.mkv","pt",cache,ff)
        ok("legenda embutida extraída", c and "Dentro do arquivo" in open(c,encoding="utf-8").read(), r.stderr[-120:])
        # ---- volume uniforme
        sh("-f","lavfi","-i","sine=f=440:d=6","-af","volume=0.05","-c:a","aac",W+"/baixo.m4a")
        l0=loud(W+"/baixo.m4a"); ok("normalize roda", mt.normalize(ff,W+"/baixo.m4a")); l1=loud(W+"/baixo.m4a")
        ok("volume ficou mais alto e perto de -16", l1>l0+8 and abs(l1+16)<4, (l0,l1))
        ok("mp4 também (vídeo copiado)", mt.normalize(ff,W+"/filme.mp4") and mt.video_codec(ff,W+"/filme.mp4")=="h264")
        # ---- H.265
        r=sh("-f","lavfi","-i","color=c=red:s=320x240:d=2","-f","lavfi","-i","sine=f=300:d=2","-shortest","-c:v","libx265","-tag:v","hvc1","-pix_fmt","yuv420p","-c:a","aac",W+"/cam.mp4")
        ok("detecta hevc", mt.video_codec(ff,W+"/cam.mp4")=="hevc", r.stderr[-100:])
        cp.CFGS["hevc"]=False
        i0=cp.prepare_local(W+"/cam.mp4",ff); ok("H.265 desligado: converte para h264", i0["path"]!=W+"/cam.mp4" and mt.video_codec(ff,i0["path"])=="h264")
        cp.CFGS["hevc"]=True
        i1=cp.prepare_local(W+"/cam.mp4",ff); ok("H.265 ligado: toca direto", i1["path"]==W+"/cam.mp4")
        sh("-i",W+"/cam.mp4","-c","copy",W+"/cam.mkv")
        i2=cp.prepare_local(W+"/cam.mkv",ff); ok("mkv hevc ligado: copia sem recodificar (hvc1)", mt.video_codec(ff,i2["path"])=="hevc")
        cp.CFGS["hevc"]=False
        i3=cp.prepare_local(W+"/filme.mp4",ff); ok("h264 mp4 segue direto", i3["path"]==W+"/filme.mp4")
        cp.CFGS["norm"]=True
        i4=cp.prepare_local(W+"/cam.mkv",ff); ok("conversão com volume uniforme", os.path.isfile(i4["path"]) and i4["path"]!=i2["path"])
        cp.CFGS["norm"]=False
        # ---- ponta a ponta com a TV falsa
        import urllib.request
        class MC:
            status=None; calls=[]; en=[]
            def register_status_listener(self,l): pass
            def stop(self): pass
            def play_media(self,url,ctype,**kw): MC.calls.append((url,ctype,kw))
            def block_until_active(self,timeout=0): pass
            def enable_subtitle(self,i): MC.en.append(i)
        class Fake:
            name=None
            def __init__(s): s.media_controller=MC(); s.status=None; s.connected=True
            class ci: host="127.0.0.1"
            cast_info=ci()
            class sc: is_connected=True
            socket_client=sc()
            def wait(self,timeout=0): pass
            def set_volume(self,v): pass
        app.cast=Fake(); app.server=cp.FileServer(); app.tools=(ff,"deno")
        for lang,txt in (("pt","Ação e emoção"),("off",None)):
            cp.CFGS["subs"]=lang; MC.calls.clear(); MC.en.clear()
            app.tracks=[{"path":W+"/filme.mp4","title":"filme"}]; app.idx=0
            onmain(lambda: app.bg(lambda: app.play_index(0)))
            for _ in range(40):
                if MC.calls: break
                time.sleep(.5)
            url,ct,kw=MC.calls[0] if MC.calls else ("","",{})
            if txt:
                su=kw.get("subtitles")
                ok("TV recebeu a legenda", bool(su) and kw.get("subtitles_lang")=="pt-BR" and MC.en==[1], kw.keys())
                u=su.replace(su.split("/")[2],"127.0.0.1:"+su.split(":")[2].split("/")[0])
                r=urllib.request.urlopen(u)
                ok("servidor entrega o vtt com CORS e tipo certo", r.headers.get("Content-Type","").startswith("text/vtt") and r.headers.get("Access-Control-Allow-Origin")=="*" and txt in r.read().decode())
            else:
                ok("legendas desligadas: nada enviado", "subtitles" not in kw and not MC.en)
        # ---- ajustes persistem
        def f():
            app.var_subs.set("en"); app.var_norm.set(True); app.var_hevc.set(True); app.apply_settings()
            return dict(app.cfg)
        c=onmain(f); ok("ajustes salvos no arquivo", c.get("subs")=="en" and c.get("norm") is True and c.get("hevc") is True)
        print("RESULTADO", sum(R), "/", len(R), flush=True)
    finally:
        onmain(lambda: os._exit(0))
threading.Thread(target=steps,daemon=True).start()
app.mainloop()
