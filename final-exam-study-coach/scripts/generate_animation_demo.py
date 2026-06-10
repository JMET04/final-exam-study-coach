#!/usr/bin/env python3
"""Generate reusable single-file HTML demos for STEM concepts."""

from __future__ import annotations

import argparse
from pathlib import Path


TEMPLATES: dict[str, str] = {}


TEMPLATES["eigenvector"] = r"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>特征向量演示</title>
<style>body{font-family:system-ui;margin:24px}canvas{border:1px solid #ccc;max-width:100%}button{margin:8px 8px 8px 0}</style>
<h1>特征向量：方向不变，只被拉伸/压缩</h1>
<canvas id="c" width="720" height="420"></canvas><br><button onclick="toggle()">播放/暂停</button><button onclick="t=0">重置</button>
<p>暂停提问：哪条向量变换后方向没变？哪条只是被拉长？</p>
<script>
const c=document.getElementById('c'),x=c.getContext('2d');let t=0,run=true;
function A(v){return [1.6*v[0],0.7*v[1]]}
function map(p){return [360+p[0]*90,210-p[1]*90]}
function vec(v,col,label){let p=map([0,0]),q=map(v);x.strokeStyle=col;x.fillStyle=col;x.lineWidth=3;x.beginPath();x.moveTo(...p);x.lineTo(...q);x.stroke();x.fillText(label,q[0]+6,q[1]-6)}
function draw(){x.clearRect(0,0,720,420);x.font='16px sans-serif';x.fillStyle='#333';for(let i=-4;i<=4;i++){let a=map([-4,i]),b=map([4,i]);x.strokeStyle='#eee';x.beginPath();x.moveTo(...a);x.lineTo(...b);x.stroke();a=map([i,-2]);b=map([i,2]);x.beginPath();x.moveTo(...a);x.lineTo(...b);x.stroke()}let k=(Math.sin(t)+1)/2;let v1=[1.8,0],v2=[1,1],w1=A(v1),w2=A(v2);vec([v1[0]*(1-k)+w1[0]*k,v1[1]*(1-k)+w1[1]*k],'#2563eb','特征向量');vec([v2[0]*(1-k)+w2[0]*k,v2[1]*(1-k)+w2[1]*k],'#dc2626','普通向量');x.fillStyle='#111';x.fillText('矩阵变换进行中：观察方向是否改变',20,30);if(run)t+=0.025;requestAnimationFrame(draw)}function toggle(){run=!run}draw();
</script></html>"""


TEMPLATES["bfs"] = r"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>BFS队列演示</title>
<style>body{font-family:system-ui;margin:24px}svg{border:1px solid #ccc;max-width:100%}.q{display:inline-block;padding:8px 12px;margin:4px;background:#dbeafe}</style>
<h1>BFS：用队列一层一层访问</h1><button onclick="step()">下一步</button><button onclick="i=0;step()">重置</button>
<svg width="720" height="300"><g id="g"></g></svg><h2>队列</h2><div id="q"></div><p id="p"></p>
<script>
const nodes={A:[100,80],B:[240,40],C:[240,130],D:[400,40],E:[400,130],F:[560,90]},edges=[['A','B'],['A','C'],['B','D'],['C','E'],['D','F'],['E','F']];
const states=[['A'],['B','C'],['C','D'],['D','E'],['E','F'],['F'],[]];let i=0,visited=[];
function render(){let g=document.getElementById('g');g.innerHTML='';for(const [a,b] of edges){let l=document.createElementNS('http://www.w3.org/2000/svg','line');l.setAttribute('x1',nodes[a][0]);l.setAttribute('y1',nodes[a][1]);l.setAttribute('x2',nodes[b][0]);l.setAttribute('y2',nodes[b][1]);l.setAttribute('stroke','#999');g.appendChild(l)}for(const [n,p] of Object.entries(nodes)){let c=document.createElementNS('http://www.w3.org/2000/svg','circle');c.setAttribute('cx',p[0]);c.setAttribute('cy',p[1]);c.setAttribute('r',24);c.setAttribute('fill',visited.includes(n)?'#86efac':'#e5e7eb');g.appendChild(c);let t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x',p[0]-5);t.setAttribute('y',p[1]+5);t.textContent=n;g.appendChild(t)}document.getElementById('q').innerHTML=(states[i]||[]).map(n=>`<span class=q>${n}</span>`).join('');document.getElementById('p').textContent='暂停提问：下一个出队的是谁？它会加入哪些邻居？'}function step(){if(i===0)visited=[];let cur=(states[i]||[])[0];if(cur&&!visited.includes(cur))visited.push(cur);i=Math.min(i+1,states.length-1);render()}render();
</script></html>"""


TEMPLATES["derivative"] = r"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>导数切线演示</title>
<style>body{font-family:system-ui;margin:24px}canvas{border:1px solid #ccc;max-width:100%}</style>
<h1>导数：割线逐渐变成切线</h1><canvas id="c" width="720" height="420"></canvas><p>暂停提问：两个点越来越近时，斜率在逼近什么？</p>
<script>
const c=document.getElementById('c'),x=c.getContext('2d');let t=0;function f(a){return 0.25*a*a}
function m(p){return [360+p[0]*80,310-p[1]*80]}function draw(){x.clearRect(0,0,720,420);x.strokeStyle='#ddd';x.beginPath();x.moveTo(0,310);x.lineTo(720,310);x.stroke();x.strokeStyle='#2563eb';x.beginPath();for(let a=-4;a<=4;a+=.05){let p=m([a,f(a)]);if(a<-3.99)x.moveTo(...p);else x.lineTo(...p)}x.stroke();let a=1,h=2*Math.exp(-t%5);let p1=m([a,f(a)]),p2=m([a+h,f(a+h)]);x.fillStyle='#dc2626';for(const p of [p1,p2]){x.beginPath();x.arc(p[0],p[1],5,0,7);x.fill()}x.strokeStyle='#dc2626';x.beginPath();x.moveTo(p1[0]-180,p1[1]-((p2[1]-p1[1])/(p2[0]-p1[0]))*180);x.lineTo(p1[0]+180,p1[1]+((p2[1]-p1[1])/(p2[0]-p1[0]))*180);x.stroke();x.fillStyle='#111';x.fillText('h = '+h.toFixed(2)+'，割线逼近切线',20,30);t+=.015;requestAnimationFrame(draw)}draw();
</script></html>"""


TEMPLATES["bayes"] = r"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>贝叶斯演示</title>
<style>body{font-family:system-ui;margin:24px}.box{display:inline-block;width:12px;height:12px;margin:2px}.sick{background:#dc2626}.ok{background:#93c5fd}.hit{outline:3px solid #111}</style>
<h1>贝叶斯：看到阳性后，样本空间被重新筛选</h1><button onclick="show()">筛选阳性</button><div id="grid"></div><p id="p">暂停提问：阳性人群里，真正患病者占多少？</p>
<script>
let filtered=false;function show(){filtered=!filtered;render()}function render(){let g=document.getElementById('grid');g.innerHTML='';for(let i=0;i<100;i++){let sick=i<5,positive=sick?i<5:i<20; if(filtered&&!positive)continue;let d=document.createElement('span');d.className='box '+(sick?'sick':'ok')+(positive?' hit':'');g.appendChild(d)}document.getElementById('p').textContent=filtered?'现在只看检测阳性的人：红色占比才是 P(患病|阳性)。':'蓝色多代表先验患病率低；黑框代表检测阳性。'}render();
</script></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a STEM animation demo HTML file.")
    parser.add_argument("template", choices=sorted(TEMPLATES))
    parser.add_argument("--output", "-o", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(TEMPLATES[args.template], encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
