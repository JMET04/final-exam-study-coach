#!/usr/bin/env python3
"""Generate reusable single-file HTML demos for STEM concepts."""

from __future__ import annotations

import argparse
from pathlib import Path


TEMPLATES: dict[str, str] = {}

TEMPLATES["eigenvector"] = r"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>特征向量演示</title>
<style>body{font-family:system-ui;margin:24px}canvas{border:1px solid #ccc;max-width:100%}button{margin:8px 8px 8px 0}</style>
<h1>特征向量：方向不变，只被拉伸或压缩</h1>
<canvas id="c" width="720" height="420"></canvas><br><button onclick="toggle()">播放/暂停</button><button onclick="t=0">重置</button>
<p>暂停提问：哪条向量变换后方向没变？哪条只是被拉长？</p>
<script>
const c=document.getElementById('c'),x=c.getContext('2d');let t=0,run=true;
function A(v){return [1.6*v[0],0.7*v[1]]}
function map(p){return [360+p[0]*90,210-p[1]*90]}
function vec(v,col,label){let p=map([0,0]),q=map(v);x.strokeStyle=col;x.fillStyle=col;x.lineWidth=3;x.beginPath();x.moveTo(...p);x.lineTo(...q);x.stroke();x.fillText(label,q[0]+6,q[1]-6)}
function draw(){x.clearRect(0,0,720,420);x.font='16px sans-serif';for(let i=-4;i<=4;i++){let a=map([-4,i]),b=map([4,i]);x.strokeStyle='#eee';x.beginPath();x.moveTo(...a);x.lineTo(...b);x.stroke();a=map([i,-2]);b=map([i,2]);x.beginPath();x.moveTo(...a);x.lineTo(...b);x.stroke()}let k=(Math.sin(t)+1)/2;let v1=[1.8,0],v2=[1,1],w1=A(v1),w2=A(v2);vec([v1[0]*(1-k)+w1[0]*k,v1[1]*(1-k)+w1[1]*k],'#2563eb','特征向量');vec([v2[0]*(1-k)+w2[0]*k,v2[1]*(1-k)+w2[1]*k],'#dc2626','普通向量');x.fillStyle='#111';x.fillText('矩阵变换进行中：观察方向是否改变',20,30);if(run)t+=0.025;requestAnimationFrame(draw)}function toggle(){run=!run}draw();
</script></html>"""

TEMPLATES["bfs"] = r"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>BFS队列演示</title>
<style>body{font-family:system-ui;margin:24px}svg{border:1px solid #ccc;max-width:100%}.q{display:inline-block;padding:8px 12px;margin:4px;background:#dbeafe}</style>
<h1>BFS：用队列一层一层访问</h1><button onclick="step()">下一步</button><button onclick="i=0;visited=[];render()">重置</button>
<svg width="720" height="300"><g id="g"></g></svg><h2>队列</h2><div id="q"></div><p id="p"></p>
<script>
const nodes={A:[100,80],B:[240,40],C:[240,130],D:[400,40],E:[400,130],F:[560,90]},edges=[['A','B'],['A','C'],['B','D'],['C','E'],['D','F'],['E','F']];
const states=[['A'],['B','C'],['C','D'],['D','E'],['E','F'],['F'],[]];let i=0,visited=[];
function render(){let g=document.getElementById('g');g.innerHTML='';for(const [a,b] of edges){let l=document.createElementNS('http://www.w3.org/2000/svg','line');l.setAttribute('x1',nodes[a][0]);l.setAttribute('y1',nodes[a][1]);l.setAttribute('x2',nodes[b][0]);l.setAttribute('y2',nodes[b][1]);l.setAttribute('stroke','#999');g.appendChild(l)}for(const [n,p] of Object.entries(nodes)){let c=document.createElementNS('http://www.w3.org/2000/svg','circle');c.setAttribute('cx',p[0]);c.setAttribute('cy',p[1]);c.setAttribute('r',24);c.setAttribute('fill',visited.includes(n)?'#86efac':'#e5e7eb');g.appendChild(c);let t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x',p[0]-5);t.setAttribute('y',p[1]+5);t.textContent=n;g.appendChild(t)}document.getElementById('q').innerHTML=(states[i]||[]).map(n=>`<span class=q>${n}</span>`).join('');document.getElementById('p').textContent='暂停提问：下一个出队的是谁？它会加入哪些邻居？'}function step(){let cur=(states[i]||[])[0];if(cur&&!visited.includes(cur))visited.push(cur);i=Math.min(i+1,states.length-1);render()}render();
</script></html>"""

TEMPLATES["derivative"] = r"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>导数切线演示</title>
<style>body{font-family:system-ui;margin:24px}canvas{border:1px solid #ccc;max-width:100%}</style>
<h1>导数：割线逐渐逼近切线</h1><canvas id="c" width="720" height="420"></canvas><p>暂停提问：两个点越来越近时，斜率在逼近什么？</p>
<script>
const c=document.getElementById('c'),x=c.getContext('2d');let t=0;function f(a){return 0.25*a*a}
function m(p){return [360+p[0]*80,310-p[1]*80]}function draw(){x.clearRect(0,0,720,420);x.strokeStyle='#ddd';x.beginPath();x.moveTo(0,310);x.lineTo(720,310);x.stroke();x.strokeStyle='#2563eb';x.beginPath();for(let a=-4;a<=4;a+=.05){let p=m([a,f(a)]);if(a<-3.99)x.moveTo(...p);else x.lineTo(...p)}x.stroke();let a=1,h=2*Math.exp(-t%5);let p1=m([a,f(a)]),p2=m([a+h,f(a+h)]);x.fillStyle='#dc2626';for(const p of [p1,p2]){x.beginPath();x.arc(p[0],p[1],5,0,7);x.fill()}x.strokeStyle='#dc2626';x.beginPath();x.moveTo(p1[0]-180,p1[1]-((p2[1]-p1[1])/(p2[0]-p1[0]))*180);x.lineTo(p1[0]+180,p1[1]+((p2[1]-p1[1])/(p2[0]-p1[0]))*180);x.stroke();x.fillStyle='#111';x.fillText('h = '+h.toFixed(2)+'，割线逼近切线',20,30);t+=.015;requestAnimationFrame(draw)}draw();
</script></html>"""

TEMPLATES["cauchy_mvt"] = r"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>柯西中值定理交互图</title>
<style>
body{font-family:system-ui;margin:24px;line-height:1.55}canvas{border:1px solid #ccc;max-width:100%;display:block}
.row{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:12px 0}button{padding:6px 10px}
input[type=range]{width:min(520px,90vw)}code{background:#f3f4f6;padding:2px 4px;border-radius:4px}
</style>
<h1>柯西中值定理：端点割线与某点切线平行</h1>
<p>把两个函数合成一条参数曲线 <code>(g(x), f(x))</code>。定理说：在区间内存在一点 ξ，使这点的切线斜率 <code>f'(ξ)/g'(ξ)</code> 等于端点割线斜率。</p>
<canvas id="c" width="760" height="440"></canvas>
<div class="row"><label>拖动 ξ：<input id="s" type="range" min="0" max="1000" value="500"></label><button onclick="jump()">定位柯西点</button></div>
<p id="info"></p>
<p><b>观察提示</b>：如果没看懂，就直接选中页面里的“参数曲线 (g(x), f(x))”“割线和切线平行”或公式那一行，用选词提问插件追问。</p>
<p>暂停提问：当红色切线和蓝色割线平行时，公式里的哪两个比值相等？</p>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),s=document.getElementById('s'),info=document.getElementById('info');
const a=.4,b=3.4;function f(x){return Math.sin(1.25*x)+.24*x*x+.25*x}function fp(x){return 1.25*Math.cos(1.25*x)+.48*x+.25}
function g(x){return x+.16*x*x}function gp(x){return 1+.32*x}
function P(x){return [g(x),f(x)]}const pa=P(a),pb=P(b);const chord=(pb[1]-pa[1])/(pb[0]-pa[0]);
function tangent(x){return fp(x)/gp(x)}function sx(X){return 80+X*150}function sy(Y){return 350-Y*115}
function lineThrough(p,m,len,col,w){ctx.strokeStyle=col;ctx.lineWidth=w;ctx.beginPath();ctx.moveTo(sx(p[0]-len),sy(p[1]-m*len));ctx.lineTo(sx(p[0]+len),sy(p[1]+m*len));ctx.stroke()}
function dot(p,col,label){ctx.fillStyle=col;ctx.beginPath();ctx.arc(sx(p[0]),sy(p[1]),6,0,7);ctx.fill();ctx.fillText(label,sx(p[0])+8,sy(p[1])-8)}
function draw(){ctx.clearRect(0,0,760,440);ctx.font='15px sans-serif';ctx.fillStyle='#111';ctx.fillText('纵轴 f(x)，横轴 g(x)：看成参数曲线 (g(x), f(x))',24,28);
ctx.strokeStyle='#e5e7eb';ctx.lineWidth=1;for(let i=0;i<7;i++){ctx.beginPath();ctx.moveTo(60+i*100,50);ctx.lineTo(60+i*100,380);ctx.stroke();ctx.beginPath();ctx.moveTo(60,70+i*50);ctx.lineTo(700,70+i*50);ctx.stroke()}
ctx.strokeStyle='#111';ctx.beginPath();ctx.moveTo(60,360);ctx.lineTo(710,360);ctx.moveTo(70,390);ctx.lineTo(70,45);ctx.stroke();
ctx.strokeStyle='#0f766e';ctx.lineWidth=3;ctx.beginPath();for(let x=a;x<=b+.001;x+=.01){let p=P(x);if(x===a)ctx.moveTo(sx(p[0]),sy(p[1]));else ctx.lineTo(sx(p[0]),sy(p[1]))}ctx.stroke();
ctx.strokeStyle='#2563eb';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(sx(pa[0]),sy(pa[1]));ctx.lineTo(sx(pb[0]),sy(pb[1]));ctx.stroke();dot(pa,'#2563eb','A');dot(pb,'#2563eb','B');
let xi=a+(b-a)*(+s.value/1000),p=P(xi),m=tangent(xi);lineThrough(p,m,.9,'#dc2626',3);dot(p,'#dc2626','ξ');
ctx.fillStyle='#111';ctx.fillText('蓝线：端点割线，斜率 = [f(b)-f(a)]/[g(b)-g(a)]',24,405);ctx.fillText('红线：ξ 点切线，斜率 = f′(ξ)/g′(ξ)',24,426);
let diff=Math.abs(m-chord);info.innerHTML=`ξ = ${xi.toFixed(3)}；割线斜率 = ${chord.toFixed(3)}；切线斜率 = ${m.toFixed(3)}；差值 = ${diff.toFixed(3)} `+(diff<.015?'已接近平行':'');}
function jump(){let best=0,err=1e9;for(let i=0;i<=1000;i++){let x=a+(b-a)*i/1000,d=Math.abs(tangent(x)-chord);if(d<err){err=d;best=i}}s.value=best;draw()}s.addEventListener('input',draw);draw();
</script></html>"""

TEMPLATES["lhopital"] = r"""<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<title>洛必达法则互动动画：函数值之比与变化速度之比</title>
<style>
body{margin:0;font-family:"Microsoft YaHei UI",system-ui,sans-serif;background:#f8fafc;color:#0f172a;line-height:1.55}
main{max-width:1120px;margin:0 auto;padding:24px}
h1{font-size:28px;margin:0 0 8px}
.sub{color:#475569;margin:0 0 18px}
.layout{display:grid;grid-template-columns:minmax(0,720px) minmax(280px,1fr);gap:18px;align-items:start}
.panel{background:#fff;border:1px solid #dbe3ef;border-radius:8px;padding:14px;box-shadow:0 1px 2px #00000010}
canvas{width:100%;height:auto;border:1px solid #cbd5e1;border-radius:6px;background:#fff}
button,select{font:inherit;border:1px solid #94a3b8;border-radius:6px;background:#fff;padding:7px 10px;margin:4px 6px 4px 0}
button.primary{background:#0f766e;color:#fff;border-color:#0f766e}
input[type=range]{width:100%}
.metric{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
.metric div{background:#f1f5f9;border-radius:6px;padding:8px}
.tag{font-weight:700;color:#0f766e}
.warn{color:#b45309}
code{background:#e2e8f0;border-radius:4px;padding:2px 5px}
ol{padding-left:22px}
@media (max-width:900px){.layout{grid-template-columns:1fr}}
</style>
<main>
<h1>洛必达法则：看谁“趋近得更快”</h1>
<p class="sub">基础原理：当分子和分母都趋近于 0 或都趋近于无穷时，直接看函数值很难判断比值。洛必达把问题换成“比较它们在附近的变化速度”，也就是比较导数。</p>
<div class="layout">
  <section class="panel">
    <canvas id="c" width="900" height="540"></canvas>
    <div>
      <button class="primary" id="play">播放/暂停</button>
      <button id="reset">重置</button>
      <select id="example">
        <option value="sin">例1：sin x / x，x → 0</option>
        <option value="exp">例2：(e^x - 1) / x，x → 0</option>
        <option value="ln">例3：ln x / (x - 1)，x → 1</option>
      </select>
    </div>
    <label>让 x 靠近目标点：<input id="slider" type="range" min="0" max="1000" value="140"></label>
  </section>
  <aside class="panel">
    <h2>观看目标</h2>
    <p>先看左图里两条曲线的高度都在变小，再看右侧数字：<span class="tag">函数值之比</span> 会逐渐接近 <span class="tag">导数之比</span>。</p>
    <h2>动画观察</h2>
    <ol>
      <li>先确认直接代入是不是 <code>0/0</code> 或 <code>∞/∞</code>。</li>
      <li>观察蓝色分子和红色分母谁变化更快。</li>
      <li>看 <code>f(x)/g(x)</code> 是否靠近 <code>f'(x)/g'(x)</code>。</li>
    </ol>
    <h2>公式连接</h2>
    <p>当 x 离目标点很近时，函数可以近似看成切线：</p>
    <p><code>f(x) ≈ f'(a)(x-a)</code>，<code>g(x) ≈ g'(a)(x-a)</code></p>
    <p>所以：</p>
    <p><code>f(x)/g(x) ≈ f'(a)/g'(a)</code></p>
    <div class="metric">
      <div>当前 x<br><b id="mx"></b></div>
      <div>判型<br><b id="type"></b></div>
      <div>函数值比 f/g<br><b id="ratio"></b></div>
      <div>导数比 f'/g'<br><b id="dratio"></b></div>
    </div>
    <p id="note" class="warn"></p>
  </aside>
</div>
<section class="panel" style="margin-top:18px">
  <h2>看完立刻做</h2>
  <p>判断下面能不能直接用洛必达，并写出求导后的式子：</p>
  <p><code>lim x→0 (e^x - 1) / x</code></p>
  <p>你回我：“能/不能，因为……；求导后变成……”。</p>
</section>
</main>
<script>
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
const slider=document.getElementById('slider'),playBtn=document.getElementById('play'),resetBtn=document.getElementById('reset'),example=document.getElementById('example');
const mx=document.getElementById('mx'),typeEl=document.getElementById('type'),ratioEl=document.getElementById('ratio'),dratioEl=document.getElementById('dratio'),note=document.getElementById('note');
let running=true,dir=1;
const configs={
  sin:{a:0,start:1.15,min:.035,name:'sin x / x',f:x=>Math.sin(x),g:x=>x,fp:x=>Math.cos(x),gp:x=>1,xmin:-1.35,xmax:1.35,ymin:-1.2,ymax:1.2,type:'0/0'},
  exp:{a:0,start:1.05,min:.035,name:'(e^x - 1) / x',f:x=>Math.exp(x)-1,g:x=>x,fp:x=>Math.exp(x),gp:x=>1,xmin:-1.1,xmax:1.25,ymin:-1.1,ymax:2.4,type:'0/0'},
  ln:{a:1,start:2.25,min:.045,name:'ln x / (x - 1)',f:x=>Math.log(x),g:x=>x-1,fp:x=>1/x,gp:x=>1,xmin:.25,xmax:2.4,ymin:-1.5,ymax:1.7,type:'0/0'}
};
function cfg(){return configs[example.value]}
function currentX(){const c=cfg();const t=+slider.value/1000;return c.a+c.min+(c.start-c.a-c.min)*t}
function sx(x){const c=cfg();return 70+(x-c.xmin)/(c.xmax-c.xmin)*700}
function sy(y){const c=cfg();return 465-(y-c.ymin)/(c.ymax-c.ymin)*385}
function drawAxes(){const c=cfg();ctx.strokeStyle='#e2e8f0';ctx.lineWidth=1;for(let i=0;i<=8;i++){let x=70+i*87.5;ctx.beginPath();ctx.moveTo(x,60);ctx.lineTo(x,465);ctx.stroke()}for(let i=0;i<=6;i++){let y=60+i*67.5;ctx.beginPath();ctx.moveTo(70,y);ctx.lineTo(770,y);ctx.stroke()}ctx.strokeStyle='#334155';ctx.beginPath();ctx.moveTo(70,sy(0));ctx.lineTo(790,sy(0));ctx.moveTo(sx(c.a),50);ctx.lineTo(sx(c.a),480);ctx.stroke();ctx.fillStyle='#334155';ctx.fillText('目标点 a',sx(c.a)+6,52)}
function plot(fn,color,label){const c=cfg();ctx.strokeStyle=color;ctx.lineWidth=3;ctx.beginPath();let first=true;for(let x=c.xmin;x<=c.xmax;x+=(c.xmax-c.xmin)/500){let y=fn(x);if(!Number.isFinite(y))continue;let px=sx(x),py=sy(y);if(first){ctx.moveTo(px,py);first=false}else ctx.lineTo(px,py)}ctx.stroke();ctx.fillStyle=color;ctx.fillText(label,790, label==='f(x)'?96:122)}
function tangentLine(x,fn,df,color){const m=df(x),y=fn(x),len=(cfg().xmax-cfg().xmin)*.18;ctx.strokeStyle=color;ctx.lineWidth=2;ctx.setLineDash([7,5]);ctx.beginPath();ctx.moveTo(sx(x-len),sy(y-m*len));ctx.lineTo(sx(x+len),sy(y+m*len));ctx.stroke();ctx.setLineDash([])}
function dot(x,y,color,label){ctx.fillStyle=color;ctx.beginPath();ctx.arc(sx(x),sy(y),6,0,Math.PI*2);ctx.fill();ctx.fillText(label,sx(x)+8,sy(y)-8)}
function drawBars(fv,gv,fr,dr){const baseX=70,baseY=510,scale=80;ctx.fillStyle='#2563eb';ctx.fillRect(baseX,baseY-Math.abs(fv)*scale,30,Math.abs(fv)*scale);ctx.fillStyle='#dc2626';ctx.fillRect(baseX+45,baseY-Math.abs(gv)*scale,30,Math.abs(gv)*scale);ctx.fillStyle='#0f172a';ctx.fillText('高度条：蓝 f(x)，红 g(x)。越靠近目标点，高度越小，速度比更关键。',120,506);ctx.fillText('f/g ≈ '+fr.toFixed(5)+'    derivative ratio ≈ '+dr.toFixed(5),120,530)}
function draw(){const c=cfg(),x=currentX(),fv=c.f(x),gv=c.g(x),fr=fv/gv,dr=c.fp(x)/c.gp(x);ctx.clearRect(0,0,900,540);ctx.font='16px Microsoft YaHei UI, sans-serif';ctx.fillStyle='#0f172a';ctx.fillText('例子：'+c.name+'。让 x 靠近目标点，比较函数值之比和导数之比。',24,30);drawAxes();plot(c.f,'#2563eb','f(x)');plot(c.g,'#dc2626','g(x)');tangentLine(x,c.f,c.fp,'#2563eb');tangentLine(x,c.g,c.gp,'#dc2626');dot(x,fv,'#2563eb','f(x)');dot(x,gv,'#dc2626','g(x)');ctx.strokeStyle='#64748b';ctx.setLineDash([4,4]);ctx.beginPath();ctx.moveTo(sx(x),sy(fv));ctx.lineTo(sx(x),sy(gv));ctx.stroke();ctx.setLineDash([]);drawBars(fv,gv,fr,dr);mx.textContent=x.toFixed(4);typeEl.textContent=c.type;ratioEl.textContent=fr.toFixed(6);dratioEl.textContent=dr.toFixed(6);note.textContent=Math.abs(fr-dr)<.02?'现在已经很接近：这就是洛必达把“函数值比”转成“变化速度比”的直观含义。':'继续让 x 靠近目标点，观察两个比值是否越来越接近。'}
function tick(){if(running){let v=+slider.value+dir*3;if(v>1000){v=1000;dir=-1}else if(v<0){v=0;dir=1}slider.value=v}draw();requestAnimationFrame(tick)}
slider.addEventListener('input',draw);example.addEventListener('change',()=>{slider.value=140;dir=1;draw()});playBtn.onclick=()=>running=!running;resetBtn.onclick=()=>{slider.value=140;dir=1;running=false;draw()};tick();
</script>
</html>"""

TEMPLATES["bayes"] = r"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>贝叶斯演示</title>
<style>body{font-family:system-ui;margin:24px}.box{display:inline-block;width:12px;height:12px;margin:2px}.sick{background:#dc2626}.ok{background:#93c5fd}.hit{outline:3px solid #111}</style>
<h1>贝叶斯：看到阳性后，样本空间被重新筛选</h1><button onclick="show()">筛选阳性</button><div id="grid"></div><p id="p">暂停提问：阳性人群里，真正患病者占多少？</p>
<script>
let filtered=false;function show(){filtered=!filtered;render()}function render(){let g=document.getElementById('grid');g.innerHTML='';for(let i=0;i<100;i++){let sick=i<5,positive=sick?i<5:i<20;if(filtered&&!positive)continue;let d=document.createElement('span');d.className='box '+(sick?'sick':'ok')+(positive?' hit':'');g.appendChild(d)}document.getElementById('p').textContent=filtered?'现在只看检测阳性的人：红色占比才是 P(患病|阳性)。':'蓝色多代表先验患病率低；黑框代表检测阳性。'}render();
</script></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a STEM animation demo HTML file.")
    parser.add_argument("template", choices=sorted(TEMPLATES))
    parser.add_argument("--output", "-o", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(TEMPLATES[args.template], encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
