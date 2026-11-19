import os, sys, json, time, shutil
import tempfile; S=tempfile.mkdtemp(prefix="tv_")
H=f"{S}/hc"; shutil.rmtree(H,ignore_errors=True); os.makedirs(H); os.environ["HOME"]=H
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import livingplay as cp
C=f"{H}/videos"; os.makedirs(C); cp.CFGS["cache"]=C; R=[]
def ok(n,c,x=""): R.append(bool(c)); print(("OK     " if c else "FALHOU ")+n,x)
def w(name,size=1000,mtime=None):
    p=os.path.join(C,name); open(p,"wb").write(b"x"*size)
    if mtime: os.utime(p,(mtime,mtime))
    return p
def vid(i,mode="video",size=5000,age=0):
    m=w(f"{i}.mp4",size,time.time()-age); j=os.path.join(C,f"{i}.{mode}.json")
    json.dump({"path":m,"ctype":"video/mp4","title":"t"},open(j,"w")); os.utime(j,(time.time()-age,)*2); return m,j
a1,aj=vid("aaaaaaaaaaa"); b1,bj=vid("bbbbbbbbbbb",age=1000,size=8000)
w("aaaaaaaaaaa.f137.mp4"); w("ccccccccccc.mp4.part"); w("local_0123456789ab.mp4",3000); w("local_0123456789ab.mp4.part.mp4")
orph=os.path.join(C,"ddddddddddd.video.json"); json.dump({"path":C+"/ddddddddddd.mp4","ctype":"video/mp4"},open(orph,"w"))
# ARQUIVOS DO USUÁRIO (nunca podem ser tocados)
mine=[w("contrato.pdf"),w("foto casamento.jpg"),w("ferias.mp4"),w("Aula_YouTube_final.mp4"),w("notas.json"),w("video.mp4"),w("aaaaaaaaaaa.docx"),w("tese.video.json")]
os.makedirs(C+"/sub"); mine.append(w("sub/aaaaaaaaaaa.mp4"))
outside=os.path.join(H,"fora.txt"); open(outside,"w").write("x"); os.symlink(outside,C+"/eeeeeeeeeee.mp4")
inv=cp.cache_inventory()
names=lambda k:sorted(os.path.basename(x[0]) for x in inv[k])
ok("vídeos = só os com arquivo de controle do programa", names("videos")==sorted(["aaaaaaaaaaa.mp4","aaaaaaaaaaa.video.json","bbbbbbbbbbb.mp4","bbbbbbbbbbb.video.json"]), names("videos"))
ok("cache = parciais, fragmentos, convertidos e sobras", names("temp")==sorted(["aaaaaaaaaaa.f137.mp4","ccccccccccc.mp4.part","local_0123456789ab.mp4","local_0123456789ab.mp4.part.mp4","ddddddddddd.video.json"]), names("temp"))
ok("arquivos do usuário não aparecem no inventário", not any(m in [x[0] for k in ("videos","temp") for x in inv[k]] for m in mine))
ok("symlink ignorado", "eeeeeeeeeee.mp4" not in names("videos")+names("temp"))
n,sz,k,e=cp.delete_files(inv["temp"])
ok("limpar cache apaga só o cache", n==5 and os.path.exists(a1) and os.path.exists(b1) and not os.path.exists(C+"/ccccccccccc.mp4.part"))
ok("arquivos do usuário intactos após limpar cache", all(os.path.exists(m) for m in mine) and os.path.exists(outside))
inv=cp.cache_inventory(); n,sz,k,e=cp.delete_files(inv["videos"],keep=[a1])
ok("excluir vídeos mantém o que está em uso", k==1 and os.path.exists(a1) and not os.path.exists(b1) and not os.path.exists(bj))
ok("arquivos do usuário intactos após excluir vídeos", all(os.path.exists(m) for m in mine) and os.path.islink(C+"/eeeeeeeeeee.mp4") and os.path.exists(outside))
# prune por limite: só mexe em vídeos do programa
shutil.rmtree(C); os.makedirs(C)
docs=[w("relatorio.docx",3*10**6),w("album.zip",3*10**6)]
v1=vid("fffffffffff",age=5000,size=2*10**6); v2=vid("ggggggggggg",age=100,size=2*10**6); v3=vid("hhhhhhhhhhh",age=10,size=2*10**6)
cp.CFGS["max_gb"]=3.0/1024  # ~3 MB
cp.prune()
ok("prune respeita o limite apagando o vídeo mais antigo do programa", not os.path.exists(v1[0]) and not os.path.exists(v2[0]) and os.path.exists(v3[0]), [os.path.exists(x[0]) for x in (v1,v2,v3)])
ok("prune nunca apaga arquivos do usuário", all(os.path.exists(d) for d in docs))
# pasta protegida
cp.CFGS["cache"]=H; w2=os.path.join(H,"aaaaaaaaaaa.mp4"); open(w2,"wb").write(b"x"); json.dump({"path":w2,"ctype":"video/mp4"},open(H+"/aaaaaaaaaaa.video.json","w"))
ok("pasta do usuário é protegida (inventário vazio)", cp.cache_inventory()=={"videos":[],"temp":[]} and cp.unsafe_dir(H) and cp.unsafe_dir("/"))
print("RESULTADO",sum(R),"/",len(R))
