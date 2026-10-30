"""
TolFlow - Simulator Antrean Gerbang Tol + Dashboard Earned Value
Jalankan lokal : streamlit run app.py
Deploy         : upload app.py dan requirements.txt ke GitHub, lalu deploy di share.streamlit.io
"""
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="TolFlow", page_icon="🚧", layout="wide")
st.markdown(
    "<style>header{visibility:hidden}.block-container{padding:0.5rem 0.5rem 0 0.5rem;max-width:1000px}</style>",
    unsafe_allow_html=True,
)

HTML = r"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>TolFlow</title>
<style>
:root{--bg:#f4f6f9;--card:#fff;--text:#14202e;--muted:#5d6b7a;--accent:#0b63c5;--road:#d9dee5;--line:#fff;--booth:#2b3a4d;--ok:#1f9d55;--warn:#d98e04;--bad:#d9363e;--bd:#dde3ea;
box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1720;--card:#18222e;--text:#e8eef5;--muted:#9aa9b9;--accent:#5aa8ff;--road:#2a3644;--line:#51606f;--booth:#8fa3b8;--ok:#3ecf7d;--warn:#f0b429;--bad:#ff6b73;--bd:#2a3644}}
:root[data-theme="dark"]{--bg:#0f1720;--card:#18222e;--text:#e8eef5;--muted:#9aa9b9;--accent:#5aa8ff;--road:#2a3644;--line:#51606f;--booth:#8fa3b8;--ok:#3ecf7d;--warn:#f0b429;--bad:#ff6b73;--bd:#2a3644}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
main{max-width:960px;margin:0 auto;padding:16px}
h1{margin:0;font-size:1.8rem}h2{margin:0;font-size:1.2rem}
.sub{color:var(--muted);margin:2px 0 14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:12px 14px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:12px}
.stat b{display:block;font-size:1.7rem;line-height:1.2}
.stat span{color:var(--muted);font-size:.8rem}
.chip{display:inline-block;padding:2px 10px;border-radius:99px;color:#fff;font-size:.8rem;font-weight:600}
#wrap{padding:0;overflow:hidden;margin-bottom:12px}
canvas{display:block;width:100%;height:440px}
.ctl{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px 18px;margin-bottom:12px}
.ctl label{display:flex;justify-content:space-between;font-weight:600}
.ctl label em{font-style:normal;color:var(--accent)}
input[type=range]{width:100%;accent-color:var(--accent)}
.btns{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
button{font:inherit;border:1px solid var(--bd);background:var(--card);color:var(--text);border-radius:10px;padding:8px 14px;cursor:pointer}
button.p{background:var(--accent);color:#fff;border-color:var(--accent)}
.th{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}
.th b{font-size:1.3rem}
.note{color:var(--muted);font-size:.8rem;margin-top:12px}
.tabs{display:flex;gap:8px;margin-bottom:14px}.tab{flex:1;font-weight:600}.tab.on{background:var(--accent);color:#fff;border-color:var(--accent)}
#evt{border-collapse:collapse;width:100%;min-width:300px}#evt th,#evt td{padding:4px 6px;text-align:center}
#evt input,.bac input{width:100%;font:inherit;padding:6px;border:1px solid var(--bd);border-radius:8px;background:var(--bg);color:var(--text)}
.bac{display:flex;align-items:center;gap:10px;font-weight:600;flex-wrap:wrap}.bac input{width:160px}
</style>
</head>
<body>
<main>
<header style="margin-bottom:14px"><h1>🚧 TolFlow</h1><p class="sub" style="margin:0">Lihat antrean dan biaya proyek sebelum terjadi.</p></header>
<nav class="tabs"><button class="tab on" data-t="1">🚦 Antrean Gerbang Tol</button><button class="tab" data-t="2">📈 Earned Value</button></nav>
<section id="p1">
<h2>Simulator Antrean Gerbang Tol</h2>
<p class="sub">Contoh kasus: plaza tol Ramp On dan Ramp Off Trihanggo, Paket 2.2B. Geser pengaturan dan lihat antrean berubah langsung.</p>

<div class="stats">
<div class="card stat"><b id="sQ">0</b><span>Antrean sekarang (kendaraan)</span></div>
<div class="card stat"><b id="sM">0</b><span>Antrean terpanjang</span></div>
<div class="card stat"><b id="sW">0 dtk</b><span>Rata-rata waktu tunggu (simulasi)</span></div>
<div class="card stat"><b id="sR">0%</b><span>Beban gardu · <i class="chip" id="sC">-</i></span></div>
</div>

<div class="card" id="wrap"><canvas id="cv"></canvas></div>

<div class="card ctl">
<div><label>Jumlah gardu <em id="vC"></em></label><input type="range" id="c" min="1" max="10" step="1" value="3"></div>
<div><label>Kedatangan (kendaraan/menit) <em id="vL"></em></label><input type="range" id="l" min="5" max="90" step="1" value="30"></div>
<div><label>Waktu layanan (detik/kendaraan) <em id="vS"></em></label><input type="range" id="s" min="4" max="20" step="1" value="8"></div>
<div><label>Kecepatan simulasi <em id="vK"></em></label><input type="range" id="k" min="1" max="30" step="1" value="6"></div>
</div>

<div class="btns">
<button class="p" id="bp">Jeda</button>
<button id="br">Ulang</button>
<button data-p="2,8,8">Skenario sepi</button>
<button data-p="3,25,8">Skenario normal</button>
<button data-p="4,45,8">Skenario jam sibuk</button>
<button data-p="3,60,8">Jam sibuk, gardu kurang</button>
</div>

<div class="card th">
<div><span class="sub">Teori antrean (Erlang C)</span><br><b id="tW">-</b><br><span class="sub">rata-rata tunggu menurut rumus</span></div>
<div><span class="sub">Rekomendasi</span><br><b id="tR">-</b><br><span class="sub">gardu minimum agar beban kurang dari 80% dan tunggu 30 detik atau kurang</span></div>
</div>
<p class="note">Angka pada skenario hanya ilustrasi, bukan data lalu lintas proyek. Kedatangan acak (Poisson), waktu layanan acak (eksponensial), kendaraan memilih antrean terpendek.</p>
</section>
<section id="p2" hidden>
<h2>Dashboard Earned Value</h2>
<p class="sub">Isi anggaran dan nilai kumulatif tiap periode (misalnya minggu). Indikator biaya dan jadwal dihitung otomatis dari periode terakhir yang terisi.</p>
<div class="card" style="margin-bottom:12px"><label class="bac">Anggaran total (BAC), juta rupiah <input type="number" id="bac" value="1000" min="0"></label></div>
<div class="card" style="margin-bottom:12px;overflow-x:auto"><table id="evt"></table>
<div class="btns" style="margin:10px 0 0"><button class="p" id="evs">Isi contoh</button><button id="evx">Kosongkan</button></div></div>
<div class="stats" id="evk"></div>
<div class="card" style="padding:0;overflow:hidden;margin-bottom:12px"><canvas id="evc2" style="height:300px"></canvas></div>
<div class="card"><b id="evm"></b></div>
<p class="note">PV adalah nilai rencana, EV nilai pekerjaan yang sudah selesai, AC biaya aktual, semuanya kumulatif. CPI dan SPI di atas 1 berarti hemat dan lebih cepat dari rencana. Angka contoh hanya ilustrasi.</p>
</section>
</main>

<script>
const $=id=>document.getElementById(id);
const cv=$('cv'),ctx=cv.getContext('2d');
const S={c:3,l:30,s:8,k:6,pause:false};
let t=0,cars=[],booths=[],maxQ=0,waits=[],W=600,H=440,TH={};
const COLORS=['#e5484d','#3b82f6','#f59e0b','#10b981','#8b5cf6','#ec4899','#64748b','#06b6d4'];

function theme(){const g=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
TH={road:g('--road'),line:g('--line'),booth:g('--booth'),text:g('--text'),ok:g('--ok'),bad:g('--bad')}}
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',theme);theme();

function resize(){const d=window.devicePixelRatio||1;W=cv.clientWidth;cv.width=W*d;cv.height=H*d;ctx.setTransform(d,0,0,d,0,0)}
addEventListener('resize',resize);resize();

const load=b=>b.queue.length+(b.cur?1:0);
function shortest(){let m=Infinity,c=[];booths.forEach(b=>{const x=load(b);if(x<m){m=x;c=[b]}else if(x===m)c.push(b)});return c[Math.floor(Math.random()*c.length)]}
function setBooths(n){while(booths.length<n)booths.push({queue:[],cur:null,rem:0});
while(booths.length>n){const b=booths.pop();[...(b.cur?[b.cur]:[]),...b.queue].forEach(car=>{car.state='queue';const nb=shortest();car.b=nb;nb.queue.push(car)})}}
function reset(){t=0;cars=[];booths=[];maxQ=0;waits=[];setBooths(S.c)}
function spawn(){const b=shortest();const car={x:W/2,y:-30,c:COLORS[Math.floor(Math.random()*COLORS.length)],state:'queue',b,t0:t};cars.push(car);b.queue.push(car)}

function step(dt){
if(Math.random()<S.l/60*dt)spawn();
booths.forEach(b=>{
if(b.cur){b.rem-=dt;if(b.rem<=0){b.cur.state='leaving';b.cur=null}}
if(!b.cur&&b.queue.length){b.cur=b.queue.shift();b.cur.state='service';waits.push(t-b.cur.t0);if(waits.length>200)waits.shift();
b.rem=Math.min(3*S.s,-S.s*Math.log(1-Math.random()))}});
t+=dt;const q=booths.reduce((a,b)=>a+b.queue.length,0);if(q>maxQ)maxQ=q}

const bx=i=>(i+.5)*W/booths.length;
function rr(x,y,w,h,r){ctx.beginPath();ctx.roundRect?ctx.roundRect(x,y,w,h,r):ctx.rect(x,y,w,h);ctx.fill()}

function draw(dt){
ctx.clearRect(0,0,W,H);
const n=booths.length,lw=W/n,by=262,cw=Math.min(22,lw*.5),chh=24;
ctx.fillStyle=TH.road;ctx.fillRect(0,0,W,H);
ctx.strokeStyle=TH.line;ctx.lineWidth=1.5;ctx.setLineDash([8,8]);
for(let i=1;i<n;i++){ctx.beginPath();ctx.moveTo(i*lw,0);ctx.lineTo(i*lw,by-8);ctx.stroke()}ctx.setLineDash([]);
const sy=el=>el;
cars.forEach(car=>{
const i=booths.indexOf(car.b);let tx=car.x,ty=car.y;
if(car.state==='leaving'){ty=H+50}
else if(i>=0){tx=bx(i);const idx=car.state==='service'?-1:car.b.queue.indexOf(car);ty=idx<0?by+12:by-22-idx*(chh+4)}
car.x+=(tx-car.x)*Math.min(1,dt*7);car.y+=(ty-car.y)*Math.min(1,dt*(car.state==='leaving'?2:6));
ctx.fillStyle=car.c;rr(car.x-cw/2,car.y-chh/2,cw,chh,5);
ctx.fillStyle='rgba(255,255,255,.55)';rr(car.x-cw/2+3,car.y-chh/2+3,cw-6,6,2)});
cars=cars.filter(c=>c.y<H+30);
booths.forEach((b,i)=>{const x=bx(i),bw=Math.min(34,lw*.7);
ctx.fillStyle=TH.booth;rr(x-bw/2,by-4,bw,46,6);
ctx.fillStyle=b.cur?TH.bad:TH.ok;ctx.beginPath();ctx.arc(x,by+2,4,0,7);ctx.fill();
ctx.fillStyle=TH.text;ctx.font='bold 12px system-ui,sans-serif';ctx.textAlign='center';
ctx.fillText('G'+(i+1),x,H-14);ctx.fillText(b.queue.length,x,16)});
ctx.textAlign='left';ctx.font='11px system-ui,sans-serif';ctx.fillText('Arah gerbang tol ↓',8,H-30)}

function erlang(c,a){if(a>=c)return null;let sum=0,term=1;for(let k=0;k<c;k++){sum+=term;term*=a/(k+1)}
const top=term/(1-a/c);return top/(sum+top)}
function wq(c){const lam=S.l/60,mu=1/S.s,a=lam/mu,C=erlang(c,a);return C===null?null:C/(c*mu-lam)}

function stats(){
const q=booths.reduce((a,b)=>a+b.queue.length,0),rho=S.l*S.s/60/S.c;
$('sQ').textContent=q;$('sM').textContent=maxQ;
$('sW').textContent=(waits.length?Math.round(waits.reduce((a,b)=>a+b,0)/waits.length):0)+' dtk';
$('sR').textContent=Math.round(rho*100)+'%';
const ch=$('sC');let txt='Lancar',col='var(--ok)';
if(rho>=.95){txt='Jenuh';col='var(--bad)'}else if(rho>=.7){txt='Padat';col='var(--warn)'}
ch.textContent=txt;ch.style.background=col;
const w=wq(S.c);$('tW').textContent=w===null?'Tak berhingga (antrean terus tumbuh)':Math.round(w)+' detik';
let rec=null;for(let k=1;k<=20;k++){const x=wq(k);if(x!==null&&S.l*S.s/60/k<.8&&x<=30){rec=k;break}}
$('tR').textContent=rec?rec+' gardu':'Lebih dari 20 gardu'}

function bind(id,key,out,fn){const el=$(id);const f=()=>{S[key]=+el.value;$(out).textContent=el.value;fn&&fn()};el.oninput=f;f()}
bind('c','c','vC',()=>setBooths(S.c));bind('l','l','vL');bind('s','s','vS');bind('k','k','vK',()=>$('vK').textContent=S.k+'x');
$('bp').onclick=()=>{S.pause=!S.pause;$('bp').textContent=S.pause?'Lanjut':'Jeda'};
$('br').onclick=reset;
document.querySelectorAll('[data-p]').forEach(b=>b.onclick=()=>{const[p,l,s]=b.dataset.p.split(',');
$('c').value=p;$('l').value=l;$('s').value=s;['c','l','s'].forEach(i=>$(i).oninput());reset()});

reset();let last=performance.now(),acc=0;
function loop(now){const dt=Math.min(.05,(now-last)/1000);last=now;
if(!S.pause){let r=dt*S.k;while(r>0){const d=Math.min(.1,r);step(d);r-=d}}
draw(dt);acc+=dt;if(acc>.25){acc=0;stats()}requestAnimationFrame(loop)}
requestAnimationFrame(loop);
</script>
<script>
(function(){
const E=id=>document.getElementById(id),N=6;
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const f=x=>Math.round(x).toLocaleString('id-ID');
const SAMPLE=[[100,90,100],[250,230,260],[430,380,440],[620,520,640],[800,660,830],[1000,'','']];
let h='<tr><th>Periode</th><th>PV</th><th>EV</th><th>AC</th></tr>';
for(let i=0;i<N;i++)h+=`<tr><td>${i+1}</td>`+[0,1,2].map(j=>`<td><input type="number" min="0"></td>`).join('')+'</tr>';
E('evt').innerHTML=h;
const inp=[...document.querySelectorAll('#evt input')];
const get=(i,j)=>{const v=inp[i*3+j].value;return v===''?null:+v};
function fill(d){inp.forEach((x,k)=>x.value=d?d[Math.floor(k/3)][k%3]:'');if(d)E('bac').value=1000;calc()}
function calc(){
const bac=+E('bac').value||0;let cur=-1;
for(let i=0;i<N;i++)if(get(i,1)!==null&&get(i,2)!==null)cur=i;
const k=E('evk');
if(cur<0||!bac){k.innerHTML='';E('evm').textContent='Isi PV, EV, dan AC minimal satu periode, atau tekan Isi contoh.';draw();return}
const pv=get(cur,0)||0,ev=get(cur,1),ac=get(cur,2);
const cpi=ac>0?ev/ac:0,spi=pv>0?ev/pv:0,eac=cpi>0?bac/cpi:0,vac=bac-eac;
const lamp=(v,a,b,c)=>v>=1?[a,'var(--ok)']:v>=.9?[b,'var(--warn)']:[c,'var(--bad)'];
const [ct,cc]=lamp(cpi,'Sesuai anggaran','Waspada','Boros'),[st,sc]=lamp(spi,'Sesuai jadwal','Waspada','Terlambat');
const card=(v,l,chip,col)=>`<div class="card stat"><b>${v}</b><span>${l}${chip?` · <i class="chip" style="background:${col}">${chip}</i>`:''}</span></div>`;
k.innerHTML=card(cpi.toFixed(2),'CPI (kinerja biaya)',ct,cc)+card(spi.toFixed(2),'SPI (kinerja jadwal)',st,sc)+card(f(ev-ac),'CV, selisih biaya (juta Rp)')+card(f(ev-pv),'SV, selisih jadwal (juta Rp)')+card(f(eac),'Prakiraan biaya akhir (juta Rp)')+card(f(vac),'VAC, selisih anggaran akhir (juta Rp)');
E('evm').textContent=`Periode ${cur+1}: progres nyata ${(ev/bac*100).toFixed(1)}% dari rencana ${(pv/bac*100).toFixed(1)}%. Dengan kinerja biaya saat ini, biaya akhir diperkirakan Rp ${f(eac)} juta, ${vac<0?'melebihi':'di bawah'} anggaran sebesar Rp ${f(Math.abs(vac))} juta.`;
draw()}
function draw(){
const cv=E('evc2');if(!cv.clientWidth)return;
const d=devicePixelRatio||1,W=cv.clientWidth,H=300;cv.width=W*d;cv.height=H*d;const c=cv.getContext('2d');c.setTransform(d,0,0,d,0,0);
const bac=+E('bac').value||1;let mx=bac;
for(let i=0;i<N;i++)for(let j=0;j<3;j++){const v=get(i,j);if(v>mx)mx=v}
mx*=1.08;const L=44,R=W-14,T=34,B=H-28,X=i=>L+(R-L)*i/(N-1),Y=v=>B-(B-T)*v/mx;
c.font='11px system-ui,sans-serif';c.textBaseline='middle';
c.strokeStyle=css('--bd');c.fillStyle=css('--muted');c.lineWidth=1;
for(let g=0;g<=4;g++){const y=B-(B-T)*g/4;c.beginPath();c.moveTo(L,y);c.lineTo(R,y);c.stroke();c.textAlign='right';c.fillText(Math.round(mx*g/4),L-6,y)}
c.textAlign='center';for(let i=0;i<N;i++)c.fillText('P'+(i+1),X(i),B+14);
[[0,'PV','--accent'],[1,'EV','--ok'],[2,'AC','--bad']].forEach(([j,n,col],s)=>{
c.strokeStyle=c.fillStyle=css(col);c.lineWidth=2.5;c.beginPath();let on=false;
for(let i=0;i<N;i++){const v=get(i,j);if(v===null)continue;on?c.lineTo(X(i),Y(v)):c.moveTo(X(i),Y(v));on=true}c.stroke();
for(let i=0;i<N;i++){const v=get(i,j);if(v===null)continue;c.beginPath();c.arc(X(i),Y(v),3.5,0,7);c.fill()}
c.fillRect(L+s*80,12,12,4);c.fillStyle=css('--text');c.textAlign='left';c.fillText(n,L+s*80+18,14)});
c.strokeStyle=c.fillStyle=css('--muted');c.setLineDash([5,5]);c.lineWidth=1;c.beginPath();c.moveTo(L,Y(bac));c.lineTo(R,Y(bac));c.stroke();c.setLineDash([]);
c.textAlign='right';c.fillText('BAC',R,Y(bac)-8)}
inp.forEach(x=>x.oninput=calc);E('bac').oninput=calc;
E('evs').onclick=()=>fill(SAMPLE);E('evx').onclick=()=>fill(null);
addEventListener('resize',draw);matchMedia('(prefers-color-scheme: dark)').addEventListener('change',draw);
const tabs=document.querySelectorAll('.tab');
tabs.forEach(b=>b.onclick=()=>{tabs.forEach(x=>x.classList.toggle('on',x===b));E('p1').hidden=b.dataset.t!=='1';E('p2').hidden=b.dataset.t!=='2';if(b.dataset.t==='1')resize();else draw()});
fill(SAMPLE);
})();
</script>
</body>
</html>
"""

components.html(HTML, height=1700, scrolling=True)
