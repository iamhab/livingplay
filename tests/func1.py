import os, sys, threading, time, json, re
import tempfile; S=tempfile.mkdtemp(prefix="tv_")
H=f"{S}/hf1"; import shutil; shutil.rmtree(H,ignore_errors=True); os.makedirs(H)
os.environ["HOME"]=H; open(H+"/.livingplay.json","w").write('{"lang":"pt","terms_ok":1}'); os.environ["CP_DPI"]="120"
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imageio_ffmpeg; ff=imageio_ffmpeg.get_ffmpeg_exe()
import livingplay as cp
from i18n import T, LANG
cp.ensure_tools=lambda:(ff,"deno"); cp.update_ytdlp=lambda:True; cp.App.discover=lambda s:None
app=cp.App(); RES=[]
def ok(name,cond,extra=""):
    RES.append(bool(cond)); print(("OK     " if cond else "FALHOU ")+name, extra, flush=True)
def onmain(fn):
    box={}; ev=threading.Event()
    def run():
        try: box["v"]=fn()
        except Exception as e:
            import traceback; box["e"]=traceback.format_exc()
        ev.set()
    app.after(0,run); ev.wait(20)
    if "e" in box: print(box["e"]); RES.append(False); return None
    return box.get("v")
def widgets(w):
    for c in w.winfo_children(): yield c; yield from widgets(c)
def texts():
    out=[]
    for w in widgets(app):
        for opt in ("text",):
            try: v=w.cget(opt)
            except Exception: continue
            if isinstance(v,str) and v.strip(): out.append(v)
        if w.winfo_class()=="TCombobox":
            try: out+= [str(x) for x in w.cget("values")]+[w.get()]
            except Exception: pass
    return out
class MC:
    status=None
    def register_status_listener(self,l): pass
    def stop(self): pass
class Fake:
    name=None
    def __init__(s): s.media_controller=MC(); s.status=None; s.connected=True
    class ci: host="192.168.100.19"
    cast_info=ci()
    class sc: is_connected=True
    socket_client=sc()
    def wait(self,timeout=0): pass
    def set_volume(self,v): pass
def steps():
    time.sleep(1.5)
    # ---- Status: nome None não pode virar "None: online"
    fk=Fake(); app.devices={"Chromecast (192.168.100.19)":fk}
    onmain(lambda: app.connect("Chromecast (192.168.100.19)")); time.sleep(1.5)
    st=onmain(lambda: app.pill.text); ok("status Online com nome da TV (name=None)", st=="Online · Chromecast (192.168.100.19)" and "None" not in st, st)
    fk.socket_client.is_connected=False; app.set_online(False); time.sleep(.6)
    st=onmain(lambda: app.pill.text); ok("status Offline", st=="Offline", st)
    fk.socket_client.is_connected=True; app.cast=fk
    # poll real: espera ciclo
    app.set_online(False); time.sleep(3.8)
    st=onmain(lambda: app.pill.text); ok("poll volta a Online sozinho", st.startswith("Online"), st)
    fk.socket_client.is_connected=False; time.sleep(3.8)
    st=onmain(lambda: app.pill.text); ok("poll detecta queda -> Offline", st=="Offline", st)
    fk.socket_client.is_connected=True
    # ---- Título / nome
    ok("título da janela PT", onmain(app.title)=="Livingplay", onmain(app.title))
    # ---- estado antes de trocar idioma
    app.tracks=[{"title":"Entrevista A","id":"a","url":"ua"},{"title":"Podcast B","id":"b","url":"ub"}]
    app.idx=1; app.queue_name="Doc"; app.now_state={"title":"Podcast B","i":2,"n":2,"extra":"  ·  720p"}
    app.vol_val=33; app.msg("Teste de mensagem")
    onmain(lambda:(app.fill_list(),app.render_now(),app.link.insert(0,"http://x")))
    pt=texts()
    bad=[t for t in pt if re.search(r"m[úu]sica",t,re.I)]
    ok("nenhum texto PT com 'música'", not bad, bad[:3])
    # ---- trocar para inglês (sem reiniciar)
    onmain(lambda:(app.var_lang.set("English"),app.change_lang())); time.sleep(1.5)
    ok("idioma = en", LANG["v"]=="en")
    ok("título da janela EN", onmain(app.title)=="Livingplay", onmain(app.title))
    en=onmain(texts)
    ptw=re.compile(r"\b(Tocar|Ajustes|Fila|Procurar|Cole|Baixar|Escolher|Aparelho|Vídeo|Tema|Idioma|Nenhum|Abrir|Excluir|Renomear|Playlist[s]? salva|Conectando|Nada tocando|Pronto|Detalhes|Copiar|Controle|Qualidade|Parar|Limite|Pasta|Avançado|Endereço|Armazenamento|Reprodução|Retomar|Última|Ainda|Escuro|Claro|Compacto)\b")
    left=[t for t in en if ptw.search(t) and "Playlists" != t]
    ok("EN: sem palavras em português na interface", not left, left[:5])
    ok("EN: estado preservado (fila, now playing, volume, link)",
       onmain(lambda:(app.lst.size(), app.now_title.cget("text"), app.vol_lbl.cget("text"), app.link.get(), app.q_lbl.cget("text")))==(2,"Podcast B","33%","http://x","Playlist: Doc"),
       onmain(lambda:(app.lst.size(), app.now_title.cget("text"), app.vol_lbl.cget("text"), app.link.get(), app.q_lbl.cget("text"))))
    ok("EN: status continua Online", onmain(lambda:app.pill.text).startswith("Online"))
    ok("EN: item atual", "Item 2 of 2" in onmain(lambda:app.now_sub.cget("text")), onmain(lambda:app.now_sub.cget("text")))
    ok("idioma persistido no arquivo", json.load(open(cp.CFG))["lang"]=="en")
    # ---- voltar ao português
    onmain(lambda:(app.var_lang.set("Português (Brasil)"),app.change_lang())); time.sleep(1.5)
    ok("volta ao PT", LANG["v"]=="pt" and onmain(app.title)=="Livingplay")
    # ---- tema e tamanho ao vivo
    onmain(lambda:(app.var_theme.set("Claro"),app.apply_settings())); time.sleep(1.5)
    ok("tema claro aplicado na hora", onmain(lambda: app.cget("bg"))==cp.PALETTES["Claro"]["bg"])
    onmain(lambda:(app.var_size.set("Grande"),app.apply_settings())); time.sleep(1.5)
    ok("tamanho grande aplicado", app.size_name=="Grande")
    onmain(lambda:(app.var_theme.set("Escuro"),app.var_size.set("Compacto"),app.apply_settings())); time.sleep(1.5)
    # ---- playlists
    onmain(lambda:app.show_page("lists"))
    import dialogs as dl
    ans=iter(["Treinos","Entrevistas","Entrevistas","Podcasts"])
    dl.ask_text=lambda *a,**k: next(ans)
    dl.confirm=lambda *a,**k: True
    onmain(app.new_playlist); onmain(app.new_playlist)   # Treinos, Entrevistas
    ok("2 playlists criadas", app.pl_names()==["Entrevistas","Treinos"], app.pl_names())
    onmain(app.new_playlist)  # duplicada: "Entrevistas" de novo
    ok("nome duplicado é recusado", app.pl_names()==["Entrevistas","Treinos"])
    onmain(app.save_playlist)  # salva fila atual como "Podcasts"
    ok("salvar fila como playlist", len(app.cfg["playlists"]["Podcasts"])==2)
    onmain(lambda:(app.pl_list.selection_clear(0,"end"),app.pl_list.selection_set(app.pl_names().index("Podcasts")),app.pl_selected()))
    ok("itens da playlist selecionada aparecem", onmain(lambda:app.pl_items.size())==2 and "Podcasts" in onmain(lambda:app.pl_items_lbl.cget("text")))
    onmain(lambda:(app.pl_items.selection_set(0),app.remove_pl_item()))
    ok("remover item da playlist", len(app.cfg["playlists"]["Podcasts"])==1 and onmain(lambda:app.pl_items.size())==1)
    ans2=iter(["Podcasts 2"]); dl.ask_text=lambda *a,**k: next(ans2)
    onmain(app.rename_playlist)
    ok("renomear playlist", "Podcasts 2" in app.cfg["playlists"] and "Podcasts" not in app.cfg["playlists"])
    ok("combo rápido da aba Reproduzir lista as playlists", set(onmain(lambda:app.pl_quick.cget("values")))=={"Entrevistas","Podcasts 2","Treinos"})
    onmain(app.delete_playlist)
    ok("excluir playlist", "Podcasts 2" not in app.cfg["playlists"] and len(app.cfg["playlists"])==2)
    # abrir playlist: usa add_tracks (sem TV real/yt): intercepta
    got={}
    app.add_tracks=lambda new,replace=False,start=0,name="": got.update(n=len(new),r=replace,name=name)
    app.cfg["playlists"]["Entrevistas"]=[{"title":"E1","id":"1","url":"u1"},{"title":"E2","id":"2","url":"u2"}]
    onmain(app.refresh_lists)
    onmain(lambda:(app.pl_list.selection_clear(0,"end"),app.pl_list.selection_set(0),app.pl_selected(),app.open_playlist())); time.sleep(.8)
    ok("abrir playlist troca a fila com o nome dela", got=={"n":2,"r":True,"name":"Entrevistas"}, got)
    # ---- persistência: novo App lê o mesmo arquivo
    cfg=json.load(open(cp.CFG))
    ok("persistência: playlists/tema/tamanho/idioma no arquivo", set(cfg["playlists"])=={"Entrevistas","Treinos"} and cfg["lang"]=="pt" and cfg["theme"]=="Escuro" and cfg["size"]=="Compacto", {k:cfg.get(k) for k in("lang","theme","size")})
    print("RESULTADO",sum(RES),"/",len(RES)); app.ui(app.on_close)
threading.Thread(target=steps,daemon=True).start(); app.mainloop()
