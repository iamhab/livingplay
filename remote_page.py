# -*- coding: utf-8 -*-
"""Página de controle para o celular. Os textos @@chave@@ vêm da tabela de idiomas (mesmo idioma do programa)."""

REMOTE_HTML = r"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name=color-scheme content="light dark"><title>@@app_title@@</title><style>
:root{--bg:#f4f6fb;--sf:#fff;--sf2:#eef1f7;--bd:#d9dfeb;--tx:#172033;--mu:#667089;--ac:#2f6bff;--acs:#e3ecff;--on:#fff;--ok:#12a066;--bad:#d33a3a}
@media(prefers-color-scheme:dark){:root{--bg:#0f1115;--sf:#171a21;--sf2:#222733;--bd:#2c3240;--tx:#e9ecf3;--mu:#8f98ad;--ac:#5b8cff;--acs:#26335a;--ok:#3ddc97;--bad:#ff6b6b}}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.35 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
padding:14px max(14px,env(safe-area-inset-right)) max(24px,env(safe-area-inset-bottom)) max(14px,env(safe-area-inset-left))}
main{max-width:520px;margin:auto}
header{display:flex;align-items:center;gap:10px;margin:2px 0 12px}
.logo{width:34px;height:34px;display:grid;place-items:center}svg.ic{width:34px;height:34px}
header h1{font-size:16px;margin:0;font-weight:650;flex:1;line-height:1.2}
#net{display:none;background:var(--bad);color:#fff;border-radius:12px;padding:10px 12px;margin-bottom:10px;font-size:14px}
.card{background:var(--sf);border:1px solid var(--bd);border-radius:18px;padding:16px;margin-bottom:12px}
.chip{display:inline-flex;align-items:center;gap:7px;background:var(--sf2);border:1px solid var(--bd);border-radius:99px;padding:5px 12px;font-size:13px;color:var(--mu)}
.dot{width:9px;height:9px;border-radius:50%;background:var(--bad)}.dot.on{background:var(--ok)}
#title{font-size:21px;font-weight:650;margin:12px 0 2px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;word-break:break-word}
#sub{color:var(--mu);font-size:14px;min-height:19px}
input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:36px;background:transparent;margin:6px 0 0;padding:0}
input[type=range]::-webkit-slider-runnable-track{height:6px;border-radius:3px;background:var(--sf2);border:1px solid var(--bd)}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:24px;height:24px;border-radius:50%;background:var(--ac);margin-top:-10px;border:3px solid var(--sf)}
input[type=range]::-moz-range-track{height:6px;border-radius:3px;background:var(--sf2)}
input[type=range]::-moz-range-thumb{width:20px;height:20px;border-radius:50%;background:var(--ac);border:3px solid var(--sf)}
.times{display:flex;justify-content:space-between;color:var(--mu);font-size:13px;margin-top:-4px}
.tr{display:grid;grid-template-columns:1fr 1fr 1.35fr 1fr 1fr;gap:8px;margin:14px 0 10px;align-items:center}
.tr2{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
button,select,input[type=text]{font:inherit;color:var(--tx)}
button{border:1px solid var(--bd);background:var(--sf2);border-radius:16px;min-height:52px;display:grid;place-items:center;cursor:pointer;padding:0 8px}
button:active{transform:scale(.97)}
button.big{min-height:66px;background:var(--ac);border-color:var(--ac);color:var(--on);border-radius:20px}
button.on{background:var(--acs);border-color:var(--ac);color:var(--ac)}
button b{font-size:14px;font-weight:650}
svg{width:24px;height:24px;fill:currentColor}svg.s{fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.big svg{width:30px;height:30px}
.seg{display:grid;grid-template-columns:1fr 1fr;background:var(--sf2);border:1px solid var(--bd);border-radius:99px;padding:3px;gap:3px}
.seg button{min-height:44px;border:0;border-radius:99px;background:transparent;color:var(--mu);font-weight:600}
.seg button.on{background:var(--ac);color:var(--on)}
.lbl{font-size:13px;color:var(--mu);margin:0 0 8px;font-weight:600;letter-spacing:.02em}
.vol{display:flex;align-items:center;gap:10px;color:var(--mu)}.vol input{flex:1}.vol span{width:44px;text-align:right;font-size:14px}
.field{width:100%;border:1px solid var(--bd);background:var(--sf2);border-radius:14px;min-height:50px;padding:0 14px;font:inherit}
select.field{appearance:none}
.row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}
.row button{min-height:50px;font-weight:650}.row .pri{background:var(--ac);color:var(--on);border-color:var(--ac)}
#q{max-height:40vh;overflow:auto;margin:0 -6px}
#q div{padding:12px 10px;border-radius:12px;display:flex;gap:10px;align-items:baseline;cursor:pointer}
#q div:active{background:var(--sf2)}#q .cur{background:var(--acs);color:var(--ac);font-weight:650}
#q i{font-style:normal;color:var(--mu);min-width:24px;font-size:14px}#q .cur i{color:var(--ac)}
#empty{color:var(--mu);font-size:14px;padding:6px 2px}
#msg{color:var(--mu);font-size:13px;margin-top:10px;min-height:18px}
</style></head><body><main>
<header><div class=logo><svg class=ic viewBox="0 0 1430.35 1430.35" aria-hidden="true"><circle cx="715.175" cy="715.175" r="715.175" fill="#2F6BFF"/><path fill="#fff" fill-rule="evenodd" d="M997.33 913.52l0 -396.69c0,-45.41 64.26,-45.41 64.26,0l0 396.69c0,45.41 -64.26,45.41 -64.26,0zM832.51 905.14l0 -379.93c0,-59.6 67.05,-51.71 67.05,-5.59l0 391.11c0,46.12 -67.05,54.01 -67.05,-5.59zM405.08 947.05c-19.63,0 -36.32,-8.37 -36.32,-27.94l0 -407.87c0,-21.48 23.04,-40.47 61.63,-16.93 79.83,48.72 181.05,103.41 264.05,152.2 16.88,9.93 30.35,18.26 47.71,27.72 24.85,13.53 37.28,18.41 37.28,43.74 0,25.27 -52.02,46.49 -84.99,65.87l-95.74 55.12c-17.22,9.62 -31.28,17.72 -47.8,27.63l-118.76 68.4c-7.95,4.81 -16.41,12.06 -27.06,12.06zM433.02 857.65c8.46,-2.26 23.63,-12.22 30.89,-16.6l60.08 -34.9c11.06,-6.71 21.38,-12.62 31.95,-18.34 20.25,-10.97 39.54,-22.45 60.27,-34.71l62.65 -40.72 -245.84 -139.68 0 284.95zz"/></svg></div><h1>@@app_title@@</h1></header>
<div id=net>@@r_offline@@</div>
<section class=card>
 <span class=chip><i class=dot id=dot></i><span id=dev>—</span></span>
 <div id=title>@@r_nothing@@</div><div id=sub></div>
 <input type=range id=p min=0 max=100 value=0 aria-label="@@r_now@@">
 <div class=times><span id=a>0:00</span><span id=d>0:00</span></div>
 <div class=tr>
  <button id=bprev onclick="c('prev')" aria-label=prev><svg viewBox="0 0 24 24"><path d="M6 6h2v12H6zM9.5 12L18 6v12z"/></svg></button>
  <button onclick="c('skip',-10)"><b>−10</b></button>
  <button class=big id=pp onclick="c('playpause')" aria-label=play></button>
  <button onclick="c('skip',10)"><b>+10</b></button>
  <button id=bnext onclick="c('next')" aria-label=next><svg viewBox="0 0 24 24"><path d="M16 6h2v12h-2zM14.5 12L6 6v12z"/></svg></button>
 </div>
 <div class=tr2>
  <button id=sh onclick="c('shuffle')"><svg class=s viewBox="0 0 24 24"><path d="M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/></svg></button>
  <button id=rp onclick="c('repeat')"><svg class=s viewBox="0 0 24 24"><path d="M17 1l4 4-4 4M3 11V9a4 4 0 0 1 4-4h14M7 23l-4-4 4-4M21 13v2a4 4 0 0 1-4 4H3"/></svg></button>
  <button onclick="c('stop')"><svg viewBox="0 0 24 24"><path d="M7 7h10v10H7z"/></svg></button>
 </div>
 <div class=vol style="margin-top:14px"><svg class=s viewBox="0 0 24 24"><path d="M11 5L6 9H2v6h4l5 4V5zM15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14"/></svg>
  <input type=range id=v min=0 max=100 value=50 aria-label="@@r_vol@@"><span id=vl>50%</span></div>
 <div id=msg></div>
</section>
<section class=card><p class=lbl>@@r_playon@@</p>
 <div class=seg><button id=tgc onclick="c('target','cast')">@@tgt_cast@@</button><button id=tgp onclick="c('target','pc')">@@tgt_pc@@</button></div></section>
<section class=card><p class=lbl>@@r_addvideo@@</p>
 <input type=text class=field id=u placeholder="@@remote_ph@@" inputmode=url autocapitalize=off autocomplete=off spellcheck=false>
 <div class=row><button class=pri onclick="add('playnow')">@@r_play@@</button><button onclick="add('add')">@@r_add@@</button></div>
 <div class=row style="grid-template-columns:1fr 1fr"><select class=field id=pl onchange="if(this.value)c('openpl',this.value);this.value=''"><option value="">@@r_lists@@</option></select>
 <select class=field id=sl onchange="c('sleep',this.value)"><option value=0>@@r_timer@@</option><option value=15>15 min</option><option value=30>30 min</option><option value=60>60 min</option><option value=90>90 min</option><option value=end>@@r_end@@</option></select></div></section>
<section class=card><p class=lbl>@@r_queue@@</p><div id=empty>@@r_empty@@</div><div id=q></div></section>
</main><script>
const K=new URLSearchParams(location.search).get('k')||'',$=i=>document.getElementById(i);let busy=0,bad=0,timer;
const IC={play:'<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>',pause:'<svg viewBox="0 0 24 24"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>'};
const api=(p,b)=>fetch(p+'?k='+encodeURIComponent(K),{method:b?'POST':'GET',body:b?JSON.stringify(b):undefined}).then(r=>{if(!r.ok)throw 0;return r.json()});
const c=(name,arg)=>api('/api/cmd',{name,arg}).then(ok).catch(fail);
const add=n=>{const x=$('u').value.trim();if(x){c(n,x);$('u').value=''}};
const f=x=>{x=Math.max(0,x|0);const h=x/3600|0,m=(x%3600)/60|0,s=x%60;return (h?h+':'+String(m).padStart(2,'0'):m)+':'+String(s).padStart(2,'0')};
const P=$('p'),V=$('v'),esc=t=>String(t).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
P.oninput=()=>{busy=1;$('a').textContent=f(P.value)};P.onchange=()=>{busy=0;c('seek',P.value)};
let vb=0;V.oninput=()=>{vb=Date.now();$('vl').textContent=V.value+'%'};V.onchange=()=>{c('vol',V.value)};
function ok(s){bad=0;$('net').style.display='none';render(s)}
function fail(){if(++bad>=2)$('net').style.display='block'}
function render(s){if(!s)return;
 $('dev').textContent=s.device||'—';$('dot').className='dot'+(s.online?' on':'');
 $('tgc').className=s.target=='cast'?'on':'';$('tgp').className=s.target=='pc'?'on':'';
 $('title').textContent=s.title||'@@r_nothing@@';
 $('sub').textContent=s.tracks.length&&s.title?'@@r_item@@'.replace('%1',s.idx+1).replace('%2',s.tracks.length):'';
 if(!busy){P.max=s.dur||100;P.value=s.pos||0;$('a').textContent=f(s.pos);$('d').textContent=f(s.dur)}
 if(Date.now()-vb>1500){V.value=s.vol;$('vl').textContent=s.vol+'%'}
 $('sh').className=s.shuffle?'on':'';$('rp').className=s.repeat?'on':'';
 $('pp').innerHTML=s.playing?IC.pause:IC.play;$('msg').textContent=s.msg||'';
 const pl=$('pl');if(pl.options.length-1!=s.playlists.length){pl.length=1;s.playlists.forEach(n=>pl.add(new Option(n,n)))}
 $('empty').style.display=s.tracks.length?'none':'block';
 const h=s.tracks.map((x,i)=>'<div class="'+(i==s.idx&&s.title?'cur':'')+'" data-i="'+i+'"><i>'+(i+1)+'</i><span>'+esc(x)+'</span></div>').join('');
 if($('q').dataset.h!=h){$('q').innerHTML=h;$('q').dataset.h=h}}
$('q').onclick=e=>{const d=e.target.closest('[data-i]');if(d)c('play_idx',+d.dataset.i)};
function poll(){clearTimeout(timer);if(document.hidden){timer=setTimeout(poll,3000);return}
 api('/api/state').then(ok).catch(fail).finally(()=>{timer=setTimeout(poll,bad?4000:1500)})}
document.addEventListener('visibilitychange',()=>{if(!document.hidden)poll()});
$('pp').innerHTML=IC.play;poll();
</script></body></html>"""
