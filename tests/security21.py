"""Segurança e robustez: configuração estragada, páginas, servidores locais, código de acesso, limpeza e registro."""
import os, sys, threading, time, json, tempfile, socket, http.client
D=tempfile.mkdtemp(prefix="tv_"); os.environ["CP_DPI"]="120"; os.environ["HOME"]=D+"/h"; os.makedirs(os.environ["HOME"],exist_ok=True)
# configuração estragada de propósito: o programa tem que abrir mesmo assim
json.dump({"lang":"pt","terms_ok":1,"max_gb":"abc","adjust":"nan","lookahead":"x","mode":"???","theme":5,
           "playlists":{"Boa":[{"title":"a","url":"https://x.y/1"}],"Ruim":"texto"},"session":{"tracks":"x"},
           "fold":[1,2],"cache":12345},open(os.environ["HOME"]+"/.livingplay.json","w"))
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imageio_ffmpeg; ff=imageio_ffmpeg.get_ffmpeg_exe()
import livingplay as cp, dialogs
cp.ensure_tools=lambda:(ff,"deno"); cp.update_ytdlp=lambda:True; cp.App.discover=lambda s:None
R=[]
def ok(n,c,x=""): R.append(bool(c)); print(("OK     " if c else "FALHOU ")+n,x,flush=True)
app=cp.App()
ok("abre com configuração estragada", True)
ok("valores ruins viram padrão", cp.CFGS["max_gb"]==3.0 and app.lookahead==3 and app.adjust==0 and app.theme=="Claro", (cp.CFGS["max_gb"],app.lookahead,app.adjust,app.theme))
ok("playlist boa fica, ruim sai", list(app.cfg.get("playlists",{}))==["Boa"], app.cfg.get("playlists"))
def onmain(fn):
    box={}; ev=threading.Event()
    def run():
        try: box["v"]=fn()
        except Exception as e: box["e"]=e
        ev.set()
    app.after(0,run); ev.wait(20)
    if "e" in box: raise box["e"]
    return box.get("v")
def req(port, method, path, body=None, headers=None):
    c=http.client.HTTPConnection("127.0.0.1",port,timeout=10)
    c.request(method,path,body=body,headers=headers or {})
    r=c.getresponse(); data=r.read(); c.close(); return r.status, data
def steps():
    try:
        time.sleep(2)
        # ---- textos das páginas
        ok("texto da página não quebra HTML/JS", cp.page_text("It's <b> & \"x\"")=="It’s ‹b› e ”x”")
        h=cp.remote_html(); ok("página do celular sem marcadores sobrando", "@@" not in h)
        import pc_player; ok("página do PC sem marcadores sobrando", "@@" not in pc_player.pc_html())
        # ---- servidor de arquivos
        fs=cp.FileServer(); f=os.path.join(D,"v.mp4"); open(f,"wb").write(b"0123456789"*100)
        url=fs.url_for(f,"127.0.0.1"); path="/"+url.split("/",3)[3]
        st,data=req(fs.port,"GET",path); ok("arquivo registrado é entregue", st==200 and len(data)==1000)
        st,data=req(fs.port,"GET",path,headers={"Range":"bytes=10-19"}); ok("pedido parcial (Range)", st==206 and data==b"0123456789")
        st,_=req(fs.port,"GET",path,headers={"Range":"bytes=5000-"}); ok("Range fora do arquivo = 416", st==416)
        st,_=req(fs.port,"GET","/f/naoexiste/v.mp4"); ok("código errado = 404", st==404)
        st,_=req(fs.port,"GET","/f/../../../../etc/passwd"); ok("tentativa de sair da pasta = 404", st==404)
        st,_=req(fs.port,"GET","/etc/passwd"); ok("caminho qualquer = 404", st==404)
        ok("conexão parada tem tempo limite", fs.srv.RequestHandlerClass.timeout==120)
        # ---- controle remoto
        for _ in range(60):
            if app.remote: break
            time.sleep(.2)
        port=app.remote.port; tok=app.token
        ok("código de acesso tem 24 caracteres", len(tok)==24, len(tok))
        st,_=req(port,"GET","/api/state?k=errado"); ok("código errado = 403", st==403)
        st,data=req(port,"GET",f"/api/state?k={tok}"); ok("código certo = estado", st==200 and b"tracks" in data)
        st,_=req(port,"POST",f"/api/cmd?k={tok}",body=b"[1,2,3]",headers={"Content-Type":"application/json"}); ok("corpo estranho não derruba", st==200)
        st,_=req(port,"POST",f"/api/cmd?k={tok}",body=json.dumps({"name":"seek","arg":"nan"}).encode()); ok("argumento inválido não derruba", st==200)
        # Content-Length negativo no /pc/sync não pode prender a conexão
        s=socket.create_connection(("127.0.0.1",port),timeout=5)
        s.sendall(f"POST /pc/sync?k={tok} HTTP/1.1\r\nHost: x\r\nContent-Length: -5\r\n\r\n".encode())
        t0=time.time(); got=s.recv(200); s.close()
        ok("Content-Length negativo responde na hora", got.startswith(b"HTTP/1.") and time.time()-t0<3, got[:20])
        # várias tentativas erradas do próprio PC não bloqueiam o PC
        for _ in range(12): req(port,"GET","/api/state?k=errado")
        st,_=req(port,"GET",f"/api/state?k={tok}"); ok("muitos erros bloqueiam por 1 minuto (429)", st==429, st)
        app.remote.guard.fails.clear()
        # bloqueio para IP da rede
        g=cp.Guard(limit=8)
        for _ in range(8): g.fail("192.168.0.50")
        ok("8 erros de outro aparelho = bloqueio", g.blocked("192.168.0.50") and not g.blocked("192.168.0.51"))
        ok("só rede local", cp.is_lan_ip("192.168.1.2") and cp.is_lan_ip("10.0.0.1") and cp.is_lan_ip("127.0.0.1") and not cp.is_lan_ip("8.8.8.8") and not cp.is_lan_ip("lixo"))
        ok("só links http(s)", cp.valid_media_url("https://a.b/c") and not cp.valid_media_url("file:///c:/x") and not cp.valid_media_url("javascript:alert(1)") and not cp.valid_media_url("https://u:p@a.b/"))
        # troca do código de acesso
        dialogs.confirm=lambda *a,**k: True
        onmain(lambda: app.new_token(None)); new=app.token
        st,_=req(port,"GET",f"/api/state?k={tok}"); ok("código antigo deixa de valer", st==403)
        st,_=req(port,"GET",f"/api/state?k={new}"); ok("código novo vale", st==200)
        ok("código novo salvo", json.load(open(cp.CFG))["token"]==new)
        # ---- pasta sensível recusada
        from tkinter import filedialog
        filedialog.askdirectory=lambda **k: os.environ["HOME"]
        before=cp.CFGS["cache"]; onmain(app.choose_dir) if hasattr(app,"choose_dir") else None
        ok("pasta do usuário recusada como pasta de vídeos", cp.CFGS["cache"]==before, cp.CFGS["cache"])
        # ---- backup estranho não estraga nada
        bk=D+"/bk.json"; json.dump({"livingplay_backup":1,"max_gb":"zzz","theme":[1],"playlists":{"X":[{"title":"t","url":"https://a.b/c"},{"lixo":1}]}},open(bk,"w"))
        filedialog.askopenfilename=lambda **k: bk
        onmain(app.import_cfg)
        ok("backup estranho: só o que é válido entra", app.cfg["playlists"].get("X")==[{"title":"t","url":"https://a.b/c"}] and app.cfg.get("max_gb")!="zzz" and app.cfg.get("theme")!=[1], (app.cfg.get("max_gb"),app.cfg.get("theme")))
        # ---- limite de espaço não apaga o que está na fila
        c=cp.CFGS["cache"]; os.makedirs(c,exist_ok=True)
        def mkv(vid,title,size,age):
            p=f"{c}/{title} [{vid}].mp4"; open(p,"wb").write(b"x"*size)
            json.dump({"path":p,"title":title,"ctype":"video/mp4"},open(f"{c}/{vid}.video720.json","w"))
            t=time.time()-age; os.utime(p,(t,t)); os.utime(f"{c}/{vid}.video720.json",(t,t)); return p
        a=mkv("aaaaaaaaaaa","Velho na fila",600_000,9000); b=mkv("bbbbbbbbbbb","Velho fora",600_000,8000); n=mkv("ccccccccccc","Novo",600_000,10)
        cp.CFGS["max_gb"]=1_300_000/1024**3
        cp.prune(keep={a})
        ok("limite apaga o mais antigo que não está na fila", os.path.exists(a) and not os.path.exists(b) and os.path.exists(n), sorted(os.listdir(c)))
        ok("e o arquivo de controle dele", not os.path.exists(f"{c}/bbbbbbbbbbb.video720.json"))
        cp.CFGS["max_gb"]=3.0
        # ---- registro limitado
        open(cp.LOG,"w").write("x"*1_100_000); cp.log("depois")
        ok("registro de erros não cresce sem fim", os.path.getsize(cp.LOG)<1000 and os.path.exists(cp.LOG+".old"))
        # ---- contagem da fila em segundo plano não trava a tela
        app.tracks=[{"title":f"v{i}","path":f"{c}/Novo [ccccccccccc].mp4"} for i in range(300)]
        t0=time.time(); onmain(app.fill_list); dt=time.time()-t0
        ok("fila de 300 itens monta rápido", dt<1.5, round(dt,2))
        time.sleep(1.5); ok("contagem da fila chega", "300" in onmain(lambda: app.dl_lbl.cget("text")), onmain(lambda: app.dl_lbl.cget("text")))
        app.tracks=[]
        # ---- fechar não trava
        class SlowBrowser:
            def stop_discovery(self): time.sleep(30)
        app.browser=SlowBrowser(); app.destroy=lambda: None  # a janela fica (o teste ainda precisa imprimir)
        t0=time.time(); onmain(app.on_close); ok("fechar não espera a busca de TVs travada", time.time()-t0<4, round(time.time()-t0,2))
        print("RESULTADO",sum(R),"/",len(R))
    except BaseException as e:
        import traceback; traceback.print_exc(); print("ERRO",e)
    finally:
        sys.stdout.flush()
        os._exit(0)
threading.Thread(target=steps,daemon=True).start()
app.mainloop()
