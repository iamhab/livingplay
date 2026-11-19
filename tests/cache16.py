import os, sys, tempfile, json
D=tempfile.mkdtemp(prefix="tv_"); os.environ["HOME"]=D; os.environ["USERPROFILE"]=D
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import livingplay as cp
R=[]
def ok(n,c,x=""): R.append(bool(c)); print(("OK     " if c else "FALHOU ")+n,x,flush=True)
cp.HOME=D; cp.CFGS["cache"]=os.path.join(D,"LivingplayCache"); os.makedirs(cp.CFGS["cache"])
c=cp.CFGS["cache"]; V="abcdefghijk"
for u in ("https://www.youtube.com/watch?v="+V,"https://youtu.be/"+V+"?t=5","https://www.youtube.com/embed/"+V,"https://www.youtube.com/live/"+V,"https://m.youtube.com/watch?feature=share&v="+V,"https://www.youtube.com/shorts/"+V):
    ok("id de "+u[:45], cp.video_id(u)==V)
ok("nada baixado -> None", cp._cached(V,"video") is None)
open(c+f"/{V}.mp4","wb").write(b"x"*5000)
i=cp._cached(V,"video"); ok("arquivo solto sem .json é reconhecido", i and i["path"].endswith(V+".mp4") and i["ctype"]=="video/mp4")
ok("e passa a ser registrado (.json)", os.path.isfile(c+f"/{V}.video.json"))
ok("modo áudio não usa vídeo", cp._cached(V,"audio") is None)
ok("outra qualidade serve", cp._cached(V,"video720")["path"].endswith(".mp4"))
os.remove(c+f"/{V}.video.json")
open(c+f"/{V}.f137.mp4","wb").write(b"x"*5000)
ok("fragmento .f137 não conta", cp._cached(V,"video")["path"].endswith(f"{V}.mp4"))
os.remove(c+f"/{V}.mp4"); ok("só fragmento -> None", cp._cached(V,"video") is None)
# pasta da versão antiga
old=os.path.join(D,"ChromecastPlayerCache"); os.makedirs(old); W="zyxwvutsrqp"
p=old+f"/{W}.mp4"; open(p,"wb").write(b"x"*5000)
json.dump({"path":p,"title":"Velho","ctype":"video/mp4"},open(old+f"/{W}.video1080.json","w"))
i=cp._cached(W,"video"); ok("vídeo da pasta antiga (qualidade 1080) é aproveitado", i and i["title"]=="Velho")
ok("áudio já baixado no modo áudio", (open(c+f"/{V}.m4a","wb").write(b"x"*5000) and cp._cached(V,"audio")["ctype"].startswith("audio")))
print("RESULTADO",sum(R),"/",len(R))
