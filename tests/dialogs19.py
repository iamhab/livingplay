import os, sys, threading, time, json, tempfile
D=tempfile.mkdtemp(prefix="tv_"); os.environ["CP_DPI"]="120"; os.environ["HOME"]=D+"/h"; os.makedirs(os.environ["HOME"],exist_ok=True)
json.dump({"lang":"pt","terms_ok":1},open(os.environ["HOME"]+"/.livingplay.json","w"))
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imageio_ffmpeg; ff=imageio_ffmpeg.get_ffmpeg_exe()
import livingplay as cp, dialogs
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
def toplevel():
    import tkinter as tk
    return [w for w in app.winfo_children() if isinstance(w,tk.Toplevel)]
def ask(fn, act):
    """Roda fn (que abre o diálogo e espera) na tela principal; 'act' mexe no diálogo."""
    res={}
    app.after(0, lambda: res.update(v=fn()))
    for _ in range(100):
        time.sleep(.05)
        if toplevel(): break
    else: return "SEM_JANELA"
    time.sleep(.3); onmain(lambda: act(toplevel()[0]))
    for _ in range(100):
        time.sleep(.05)
        if "v" in res: break
    return res.get("v","SEM_RESULTADO")
def steps():
    try:
        time.sleep(2)
        r=ask(lambda: dialogs.ask_text(app,"Salvar playlist","Nome da playlist:","Inicial"),
              lambda d:(d.entry.delete(0,"end"),d.entry.insert(0,"  Rock  "),d._ok()))
        ok("digitar nome devolve texto limpo", r=="Rock", r)
        r=ask(lambda: dialogs.ask_text(app,"t","q",""), lambda d: d._cancel())
        ok("cancelar devolve None", r is None, r)
        r=ask(lambda: dialogs.ask_text(app,"t","q","x"), lambda d:(d.entry.delete(0,"end"),d._ok()))
        ok("nome vazio devolve None", r is None, r)
        r=ask(lambda: dialogs.confirm(app,"t","Apagar?"), lambda d: d._ok())
        ok("Sim devolve True", r is True, r)
        r=ask(lambda: dialogs.confirm(app,"t","Apagar?"), lambda d: d.event_generate("<Escape>"))
        ok("Esc devolve False", r is False, r)
        r=ask(lambda: dialogs.confirm(app,"t","Apagar?",default_no=True), lambda d: d.event_generate("<Return>"))
        ok("Enter com padrão 'Não' não apaga", r is False, r)
        r=ask(lambda: dialogs.confirm(app,"t","Apagar?"), lambda d: d.protocol("WM_DELETE_WINDOW") and d.nametowidget(".") and d._cancel())
        ok("fechar devolve False", r is False, r)
        ok("nenhuma janela sobrou", not toplevel())
        # ---- aba Baixados
        c=cp.CFGS["cache"]; os.makedirs(c,exist_ok=True)
        def mk(name,size=3000): open(os.path.join(c,name),"wb").write(b"x"*size)
        mk("abcdefghijk.mp4",5000); json.dump({"path":os.path.join(c,"abcdefghijk.mp4"),"title":"Meu vídeo","ctype":"video/mp4"},open(c+"/abcdefghijk.video720.json","w"))
        mk("bcdefghijkl.m4a",4000); json.dump({"path":os.path.join(c,"bcdefghijkl.m4a"),"title":"Faixa","ctype":"audio/mp4"},open(c+"/bcdefghijkl.audio.json","w"))
        mk("solto.mp4",2000); mk("local_0123456789ab.mp4"); mk("zzzzzzzzzzz.f137.mp4"); mk("x.mp4.part.mp4"); mk("tiny.mp4",10)
        os.makedirs(c+"/visuals",exist_ok=True); mk("visuals/0123456789abcdef.mp4")
        l=cp.downloaded_files()
        names=sorted(x["title"] for x in l)
        ok("lista só os arquivos baixados (sem sobras, cópias locais e telas)", names==["Faixa","Meu vídeo","solto"], names)
        ok("tipo áudio/vídeo", {x["title"]:x["audio"] for x in l}=={"Faixa":True,"Meu vídeo":False,"solto":False})
        onmain(lambda: app.show_page("files")); time.sleep(1)
        ok("aba aparece", "files" in onmain(lambda: list(app.tab_btns)))
        ok("lista na tela", onmain(lambda: app.files_list.size())==3, onmain(lambda: app.files_list.size()))
        ok("resumo mostra quantidade", "3" in onmain(lambda: app.files_lbl.cget("text")))
        got={}
        app.mc=lambda: True
        app.add_tracks=lambda new,replace=False,start=0,name="": got.update(n=new,r=replace)
        onmain(lambda:(app.files_list.selection_set(0,1),app.play_files())); time.sleep(.5)
        ok("Tocar troca a fila", got.get("r") is True and len(got["n"])==2 and all(os.path.isfile(t["path"]) for t in got["n"]), got)
        onmain(lambda:(app.files_list.selection_clear(0,"end"),app.files_list.selection_set(0),app.play_files(add=True))); time.sleep(.5)
        ok("Juntar à fila não troca", got.get("r") is False and len(got["n"])==1)
        onmain(lambda:app.files_list.selection_clear(0,"end")); n0=onmain(lambda: app.files_list.size())
        onmain(app.play_files); ok("sem seleção não faz nada e avisa", "primeiro" in app.last_msg.lower(), app.last_msg)
        # excluir
        idx=[x["title"] for x in onmain(lambda: list(app.files_data))].index("solto")
        dialogs.confirm=lambda *a,**k: True
        onmain(lambda:(app.files_list.selection_set(idx),app.delete_files_sel())); time.sleep(1)
        ok("excluir apaga o arquivo", not os.path.exists(c+"/solto.mp4"))
        ok("a lista atualiza", onmain(lambda: app.files_list.size())==2)
        ok("telas/cópias locais intactas", os.path.exists(c+"/local_0123456789ab.mp4") and os.path.exists(c+"/visuals/0123456789abcdef.mp4"))
        dialogs.confirm=lambda *a,**k: False
        idx=[x["title"] for x in onmain(lambda: list(app.files_data))].index("Faixa")
        onmain(lambda:(app.files_list.selection_clear(0,"end"),app.files_list.selection_set(idx),app.delete_files_sel())); time.sleep(.5)
        ok("cancelar não apaga", os.path.exists(c+"/bcdefghijkl.m4a"))
        onmain(app.rebuild); time.sleep(1.5)
        ok("rebuild mantém a aba e a lista", onmain(lambda: app.files_list.size())==2 and onmain(lambda: app.cur_page)=="files")
        print("RESULTADO",sum(R),"/",len(R))
    except BaseException as e:
        import traceback; traceback.print_exc(); print("ERRO",e)
    finally:
        onmain(lambda: os._exit(0))
threading.Thread(target=steps,daemon=True).start()
app.mainloop()
