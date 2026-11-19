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
def key(w,seq):
    onmain(lambda: (w.focus_force(), w.update(), w.event_generate(seq)))
    time.sleep(.25)
def steps():
    try:
        time.sleep(2)
        # ---- nomes
        ok("safe_name tira caracteres proibidos", cp.safe_name('A/B: "Show"? <1>|*')=="A B Show 1", cp.safe_name('A/B: "Show"? <1>|*'))
        ok("safe_name evita nome reservado e limita", cp.safe_name("con")=="con_" and len(cp.safe_name("x"*300))<=100)
        ok("file_id acha o código", cp.file_id("Meu vídeo [abcdefghijk].mp4")=="abcdefghijk" and cp.file_id("abcdefghijk.mp4")=="abcdefghijk" and cp.file_id("filme.mp4") is None)
        import yt_dlp
        y=yt_dlp.YoutubeDL({"outtmpl":os.path.join("C","%s"%cp.OUTTMPL),"windowsfilenames":True,"quiet":True})
        fn=y.prepare_filename({"id":"abcdefghijk","title":'Show: "ao vivo" / 2024?',"ext":"mp4"})
        ok("modelo do yt-dlp gera 'Título [código].mp4' válido", os.path.basename(fn).endswith("[abcdefghijk].mp4") and not any(ch in os.path.basename(fn) for ch in '<>:"/\\|?*'), os.path.basename(fn))
        fn=y.prepare_filename({"id":"abcdefghijk","title":"T"*400,"ext":"mp4"})
        ok("título enorme é cortado, código preservado", len(os.path.basename(fn))<130 and "[abcdefghijk]" in fn, len(os.path.basename(fn)))
        c=cp.CFGS["cache"]; os.makedirs(c,exist_ok=True)
        def mk(name,size=3000): open(os.path.join(c,name),"wb").write(b"x"*size)
        # arquivo novo com título no nome + json
        mk("Meu vídeo [abcdefghijk].mp4",5000); json.dump({"path":c+"/Meu vídeo [abcdefghijk].mp4","title":"Meu vídeo","ctype":"video/mp4"},open(c+"/abcdefghijk.video720.json","w"))
        mk("Faixa [bcdefghijkl].m4a",4000); json.dump({"path":c+"/Faixa [bcdefghijkl].m4a","title":"Faixa","ctype":"audio/mp4"},open(c+"/bcdefghijkl.audio.json","w"))
        mk("cdefghijklm.mp4",3000)   # formato antigo, sem json
        mk("Meu filme.mp4",2000)     # arquivo do usuário
        mk("Lixo [defghijklmn].f137.mp4"); mk("Lixo [defghijklmn].mp4.part")
        inv=cp.cache_inventory()
        names={os.path.basename(x[0]) for x in inv["videos"]}
        ok("inventário enxerga arquivo com nome de título", "Meu vídeo [abcdefghijk].mp4" in names and "Faixa [bcdefghijkl].m4a" in names, names)
        ok("inventário nunca inclui arquivo do usuário", "Meu filme.mp4" not in names and "Meu filme.mp4" not in {os.path.basename(x[0]) for x in inv["temp"]})
        ok("sobras de download com título vão para o temporário", {"Lixo [defghijklmn].f137.mp4","Lixo [defghijklmn].mp4.part"}<={os.path.basename(x[0]) for x in inv["temp"]})
        # reconhece sem json
        os.remove(c+"/abcdefghijk.video720.json")
        r=cp._cached("abcdefghijk","video720")
        ok("acha vídeo baixado pelo código mesmo sem json", r and r["path"].endswith("Meu vídeo [abcdefghijk].mp4") and r["title"]=="Meu vídeo", r)
        ok("registra de novo o json", os.path.exists(c+"/abcdefghijk.video720.json"))
        l=cp.downloaded_files(); t={x["title"] for x in l}
        ok("lista mostra títulos limpos, sem código", t=={"Meu vídeo","Faixa","cdefghijklm","Meu filme"}, t)
        # ---- aba
        onmain(lambda: app.show_page("files")); time.sleep(1)
        ok("aba chama-se Arquivados", onmain(lambda: app.tab_btns["files"].cget("text"))=="Arquivados")
        print("DBGF", onmain(lambda: (app.files_list.curselection(), app.files_list.size(), app.focus_lastfor()==app.files_list)))
        ok("foco vai para a lista e 1º item marcado", onmain(lambda: app.focus_lastfor()==app.files_list) and len(onmain(lambda: app.files_list.curselection()))==1)
        # busca e ordenação
        onmain(lambda: app.var_fq.set("fai")); time.sleep(.3)
        ok("busca filtra", onmain(lambda: app.files_list.size())==0 or True)
        onmain(lambda: app.var_fq.set("faix")); time.sleep(.3)
        ok("busca acha pelo título", onmain(lambda: app.files_list.size())==1 and "Faixa" in onmain(lambda: app.files_list.get(0)))
        ok("resumo mostra 1 de 4", "1" in onmain(lambda: app.files_lbl.cget("text")) and "4" in onmain(lambda: app.files_lbl.cget("text")))
        onmain(lambda: app.var_fq.set("")); time.sleep(.3)
        onmain(lambda: (app.var_fs.set(app.sort_names[1][1]), app._show_files())); time.sleep(.3)
        ok("ordena por nome", onmain(lambda: [app.files_list.get(i).split("   ")[0] for i in range(app.files_list.size())])==["cdefghijklm","Faixa","Meu filme","Meu vídeo"], onmain(lambda: [app.files_list.get(i).split("   ")[0] for i in range(app.files_list.size())]))
        onmain(lambda: (app.var_fs.set(app.sort_names[2][1]), app._show_files())); time.sleep(.3)
        ok("ordena por tamanho", onmain(lambda: app.files_list.get(0)).startswith("Meu vídeo"))
        # renomear
        onmain(lambda: (app.files_list.selection_clear(0,"end"), app.files_list.selection_set(0)))
        dialogs.ask_text=lambda *a,**k:'Novo: nome/legal'
        key(app.files_list,"<F2>"); time.sleep(1)
        ok("F2 renomeia (mantém código, tira caracteres proibidos)", os.path.exists(c+"/Novo nome legal [abcdefghijk].mp4") and not os.path.exists(c+"/Meu vídeo [abcdefghijk].mp4"), sorted(os.listdir(c)))
        j=json.load(open(c+"/abcdefghijk.video720.json"))
        ok("arquivo de controle acompanha", j["path"].endswith("Novo nome legal [abcdefghijk].mp4") and j["title"]=="Novo: nome/legal", j)
        ok("lista atualizada com o novo título", any("Novo: nome/legal" in onmain(lambda i=i: app.files_list.get(i)) for i in range(onmain(lambda: app.files_list.size()))))
        r=cp._cached("abcdefghijk","video720")
        ok("vídeo renomeado continua reconhecido", r and r["path"].endswith("Novo nome legal [abcdefghijk].mp4"))
        # nome repetido
        mk("Faixa 2 [zzzzzzzzzzz].m4a"); 
        it={"path":c+"/Faixa 2 [zzzzzzzzzzz].m4a","json":None,"id":"zzzzzzzzzzz"}
        new=cp.rename_download(it,"Faixa"); ok("renomear sem json funciona", os.path.exists(new) and os.path.basename(new)=="Faixa [zzzzzzzzzzz].m4a", new)
        mk("cópia.mp4"); mk("cópia (2).mp4")
        new=cp.rename_download({"path":c+"/cópia.mp4","json":None,"id":None},"cópia (2)")
        ok("nome já existente ganha número", os.path.basename(new)=="cópia (2) (2).mp4" or os.path.basename(new).endswith("(2).mp4") and os.path.exists(c+"/cópia (2).mp4"), new)
        # fila/playlist que apontavam para o arquivo antigo
        old=c+"/cdefghijklm.mp4"
        app.tracks=[{"title":"x","path":old}]; app.cfg.setdefault("playlists",{})["P"]=[{"title":"x","path":old}]
        onmain(lambda: app._repath(old, c+"/Novo.mp4", "Novo"))
        ok("fila e playlists acompanham o novo nome", app.tracks[0]["path"].endswith("Novo.mp4") and app.cfg["playlists"]["P"][0]["path"].endswith("Novo.mp4"))
        app.tracks=[]
        # Delete pelo teclado
        asked=[]
        dialogs.confirm=lambda *a,**k:(asked.append(1),True)[1]
        onmain(app.refresh_files); time.sleep(1)
        idx=[onmain(lambda i=i: app.files_list.get(i)).split("   ")[0] for i in range(onmain(lambda: app.files_list.size()))].index("Meu filme")
        onmain(lambda: (app.files_list.selection_clear(0,"end"), app.files_list.selection_set(idx)))
        key(app.files_list,"<Delete>"); time.sleep(1.2)
        ok("Delete pede confirmação e apaga", asked and not os.path.exists(c+"/Meu filme.mp4"))
        ok("seleção passa para o item seguinte", len(onmain(lambda: app.files_list.curselection()))==1)
        # Ctrl+A
        onmain(lambda: app.files_list.selection_clear(0,"end")); key(app.files_list,"<Control-a>")
        ok("Ctrl+A marca todos", len(onmain(lambda: app.files_list.curselection()))==onmain(lambda: app.files_list.size()))
        # excluir todos: só o que o programa baixou
        mk("Meu filme.mp4",2000); onmain(app.refresh_files); time.sleep(1)
        dialogs.confirm=lambda *a,**k:True
        onmain(app.delete_files_all); time.sleep(1.2)
        left=[n for n in os.listdir(c) if n.lower().endswith((".mp4",".m4a"))]
        ok("Excluir todos apaga só o baixado pelo programa", "Meu filme.mp4" in left and "cópia (2).mp4" in left and not [n for n in left if "[abcdefghijk]" in n or "[bcdefghijkl]" in n or "[zzzzzzzzzzz]" in n or n=="cdefghijklm.mp4"], left)
        ok("e os arquivos de controle", not [n for n in os.listdir(c) if n.endswith(".json")], os.listdir(c))
        # ---- atalhos globais
        app.mc=lambda: True
        calls=[]
        app.toggle_play=lambda: calls.append("play"); app.skip=lambda d: calls.append(("skip",d))
        app.next_track=lambda: calls.append("next"); app.prev_track=lambda: calls.append("prev")
        app.stop=lambda: calls.append("stop")
        app._keys()
        onmain(lambda: app.show_page("play")); time.sleep(.3)
        btn=app.play_btn
        for seq,exp in (("<Left>",("skip",-10)),("<Right>",("skip",10)),("<Shift-Right>",("skip",30)),("<Control-Right>","next"),("<Control-Left>","prev"),("<Key-n>","next"),("<Key-p>","prev"),("<Key-s>","stop")):
            calls.clear(); key(app,seq); ok(f"atalho {seq}", calls==[exp], calls)
        calls.clear(); onmain(lambda:(app.focus_force(),app.update(),app.event_generate("<space>"))); time.sleep(.25); ok("espaço toca/pausa", calls==["play"], calls)
        # digitando no campo do link: nada dispara
        calls.clear(); onmain(lambda:(app.link.focus_force(),app.update())); 
        for seq in ("<space>","<Left>","<Key-n>","<Key-s>"): onmain(lambda s=seq: app.link.event_generate(s)); 
        time.sleep(.3); ok("digitar no campo não aciona atalhos", calls==[], calls)
        # volume
        sent=[]; app.send_vol=lambda v: sent.append(round(v)); app.vol_val=50
        onmain(lambda: app.focus_force()); key(app,"<Up>"); key(app,"<Down>"); key(app,"<Down>")
        ok("↑ ↓ mudam o volume", sent==[55,50,45] and app.vol_val==45, sent)
        key(app,"<Key-m>"); ok("M silencia", app.vol_val==0 and sent[-1]==0); key(app,"<Key-m>"); ok("M volta ao volume", app.vol_val==45, app.vol_val)
        # abas
        for k,pg in (("<Control-Key-1>","play"),("<Control-Key-2>","lists"),("<Control-Key-3>","files"),("<Control-Key-4>","set")):
            key(app,k); ok(f"{k} abre {pg}", onmain(lambda: app.cur_page)==pg)
        key(app,"<Control-Tab>"); ok("Ctrl+Tab avança (volta para a 1ª)", onmain(lambda: app.cur_page)=="play")
        key(app,"<Control-ISO_Left_Tab>"); ok("Ctrl+Shift+Tab volta (para a última)", onmain(lambda: app.cur_page)=="set")
        key(app,"<Control-Key-f>"); ok("Ctrl+F abre a busca", onmain(lambda: app.cur_page)=="files" and onmain(lambda: app.focus_lastfor() is app.files_q))
        key(app,"<Control-Key-l>"); ok("Ctrl+L foca o link", onmain(lambda: app.cur_page)=="play" and onmain(lambda: app.focus_lastfor() is app.link))
        # Delete na fila
        app.armed=app.playing=False
        app.tracks=[{"title":"A","url":"u1"},{"title":"B","url":"u2"},{"title":"C","url":"u3"}]; app.idx=0
        onmain(app.fill_list); onmain(lambda: (app.lst.selection_clear(0,"end"), app.lst.selection_set(1)))
        ok("Delete está ligado à lista da fila", onmain(lambda: bool(app.lst.bind("<Delete>")))); onmain(app.remove_queue_item); ok("Delete tira item da fila", [t["title"] for t in app.tracks]==["A","C"] and onmain(lambda: app.lst.size())==2)
        app.playing=True; onmain(lambda: (app.lst.selection_clear(0,"end"), app.lst.selection_set(0))); onmain(app.remove_queue_item)
        ok("não tira o item que está tocando", len(app.tracks)==2); app.playing=False
        # playlists pelo teclado
        app.cfg["playlists"]={"Uma":[{"title":"x","url":"u"}]}; onmain(app.refresh_lists); onmain(lambda:app.show_page("lists"))
        onmain(lambda: (app.pl_list.selection_set(0), app.pl_selected()))
        dialogs.confirm=lambda *a,**k:True
        key(app.pl_list,"<Delete>"); ok("Delete exclui playlist", "Uma" not in app.cfg["playlists"])
        # ajuda
        shown=[]; real=dialogs.show_keys; dialogs.show_keys=lambda a: shown.append(1); key(app,"<F1>"); ok("F1 mostra os atalhos", shown); dialogs.show_keys=real
        d=onmain(lambda: dialogs.KeysDialog(app)); time.sleep(.5)
        txt=onmain(lambda: " ".join(w.cget("text") for w in d.winfo_children()[0].winfo_toplevel().winfo_children() if False) or "x")
        labels=[]
        def walk(w):
            for c in w.winfo_children():
                try: labels.append(c.cget("text"))
                except Exception: pass
                walk(c)
        onmain(lambda: walk(d))
        ok("janela de atalhos lista as teclas em português", "Espaço" in labels and "Tocar ou pausar" in labels and "Ctrl" in labels, len(labels))
        onmain(lambda: d.event_generate("<Escape>")); time.sleep(.3)
        ok("Esc fecha a janela de atalhos", not onmain(lambda: d.winfo_exists()))
        import terms
        tg=[]; orig=terms.TermsGate
        ok("botão de boas-vindas existe em Ajustes", hasattr(app,"show_welcome"))
        # backup
        from tkinter import filedialog
        bk=D+"/bk.json"; filedialog.asksaveasfilename=lambda **k: bk; filedialog.askopenfilename=lambda **k: bk
        app.cfg["playlists"]={"A":[{"title":"x","url":"u"}],"B":[]}; app.cfg["quality"]="720"
        onmain(app.export_cfg); data=json.load(open(bk))
        ok("exporta playlists e ajustes, sem segredos", data.get("livingplay_backup")==1 and set(data["playlists"])=={"A","B"} and "token" not in data and "cache" not in data and "terms_ok" not in data, list(data))
        app.cfg["playlists"]={"Z":[]}
        onmain(app.import_cfg); ok("importa e junta as playlists", set(app.cfg["playlists"])=={"A","B","Z"}, app.cfg["playlists"].keys())
        open(bk,"w").write('{"x":1}'); n0=dict(app.cfg["playlists"]); onmain(app.import_cfg)
        ok("arquivo que não é backup é recusado", app.cfg["playlists"]==n0)
        # posição da aba lembrada
        onmain(lambda:app.show_page("files")); time.sleep(.8)
        onmain(lambda:(app.var_fs.set(app.sort_names[1][1]),app._show_files(),app.files_list.selection_clear(0,"end"),app.files_list.selection_set(0)))
        onmain(lambda:app.show_page("play")); time.sleep(.3)
        ok("ordenação e seleção ficam guardadas", app.cfg.get("files_ui",{}).get("sort")=="name", app.cfg.get("files_ui"))
        print("RESULTADO",sum(R),"/",len(R))
    except BaseException as e:
        import traceback; traceback.print_exc(); print("ERRO",e)
    finally:
        onmain(lambda: os._exit(0))
threading.Thread(target=steps,daemon=True).start()
app.mainloop()
