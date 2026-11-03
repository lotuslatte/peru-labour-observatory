import {fmt,esc,findBreak,tip,showTip,lineChart,csvRows,copyText,download} from './olp.js';
const D=JSON.parse(document.getElementById('olp-data').textContent);const id=D.id,u=D.unit,b=findBreak(D.breaks,id),DIST=D.type==='dist';
const TABS=DIST?[['reparto','Reparto'],['tendencia','Tendencia'],['datos','Datos']]
  :[['tendencia','Tendencia'],...(D.regions?[['mapa','Mapa']]:[]),...(Object.keys(D.domains).length?[['quienes','Quiénes']]:[]),['datos','Datos']];
let dom=Object.keys(D.domains)[0],cat=0,yi=D.years.length-1;const elT=document.getElementById('tabs'),el=document.getElementById('tab');
const small=()=>innerWidth<620;
const brkNote=()=>b?`<p class="r-break">${esc(b.label_es)}</p>`:'';
const chart=(cells,label)=>lineChart(el.querySelector('#ch'),[{label,cells,color:'--cat-1'}],D.years,u,b,{band:true,w:small()?380:920,h:small()?280:380,aria:label+' por año'});
function tendencia(){
  if(!DIST){el.innerHTML=`${brkNote()}<div id="ch"></div>`;chart(D.national,D.name);return;}
  const c=D.national[cat];
  el.innerHTML=`${chips(D.national.map((x,k)=>[k,x.label]),cat)}${brkNote()}<div id="ch"></div><p class="r-src">Porcentaje de los ocupados en la categoría elegida.</p>`;
  chart(c.cells,c.label);el.querySelectorAll('.r-chips button').forEach(x=>x.onclick=()=>{cat=+x.dataset.k;tendencia();});}
function chips(items,cur){return `<div class="r-chips">${items.map(([k,l])=>`<button aria-pressed="${k==cur}" data-k="${k}">${esc(l)}</button>`).join('')}</div>`;}
function mapa(){const rows=D.regions,vals=rows.map(r=>r.c.v).filter(v=>v!=null).sort((x,y)=>x-y),q=[1,2,3,4,5].map(k=>vals[Math.floor(k*vals.length/6)]),bin=v=>q.filter(t=>v>=t).length+1;
  const I=D.map.I,shape=p=>{const r=rows.find(x=>x.id===p.id);return `<path d="${p.d}" data-id="${p.id}" fill="${r&&r.c.v!=null?`var(--seq-${bin(r.c.v)})`:'var(--panel-2)'}"/>`;};
  const sorted=rows.filter(r=>r.c.v!=null).sort((x,y)=>y.c.v-x.c.v),li=a=>a.map(r=>`<li><span>${esc(r.name)}</span><span>${fmt(r.c.v,u)}</span></li>`).join('');
  const miss=rows.length-sorted.length;
  el.innerHTML=`<div class="r-map"><div><svg viewBox="${D.map.box}" role="img" aria-label="Mapa por departamento">${D.map.paths.map(shape).join('')}<path class="r-edge" d="${D.map.outline}"/><clipPath id="r-metro"><rect x="${I.x}" y="${I.y}" width="${I.s}" height="${I.s}"/></clipPath><rect class="r-inset" x="${I.x}" y="${I.y}" width="${I.s}" height="${I.s}"/><g class="r-metro" clip-path="url(#r-metro)">${D.map.inset.map(shape).join('')}<path class="r-edge" d="${D.map.insetOutline}"/></g><text class="r-inset-t" x="${I.x}" y="${I.y-8}">Lima y Callao</text></svg><div class="r-scale">${[vals[0],...q].map((v,i)=>`<span><i style="background:var(--seq-${i+1})"></i>${fmt(v,u)}</span>`).join('')}</div><p class="r-src">Cada tono parte del valor indicado. Más oscuro: valor más alto.${miss?` ${miss} departamento${miss>1?'s':''} sin dato publicable.`:''}</p></div></div>
<div><p class="r-rank-t">Más alto</p><ul class="r-rank">${li(sorted.slice(0,5))}</ul><p class="r-rank-t">Más bajo</p><ul class="r-rank">${li(sorted.slice(-5))}</ul></div></div>
<details class="r-details"><summary>Ver los ${sorted.length} departamentos con dato</summary><ul class="r-rank">${li(sorted)}</ul></details>`;
  el.querySelectorAll('path').forEach(p=>{const r=rows.find(x=>x.id===p.dataset.id);if(!r)return;p.onpointerenter=()=>p.parentNode.appendChild(p);p.onpointermove=e=>showTip(e,`<b>${esc(r.name)}</b><br>${r.c.v==null?'Sin dato':esc(fmt(r.c.v,u))}${r.c.lo!=null?`<br>IC ${esc(fmt(r.c.lo,u))} a ${esc(fmt(r.c.hi,u))}`:''}`);p.onpointerleave=()=>tip().hidden=true;});}
/* Dot-and-interval rows; the scale starts at 0 unless a value is negative. */
function dots(rows,aria){const ok=rows.filter(r=>r.c.v!=null),hi=Math.max(...ok.map(r=>r.c.hi??r.c.v)),lo=Math.min(0,...ok.map(r=>r.c.lo??r.c.v)),P=small(),W=P?380:920,LW=P?168:250,RH=P?40:46,FS=P?13:15,MX=P?24:30,H=rows.length*RH+8,X=v=>LW+(v-lo)/(hi-lo||1)*(W-LW-(P?72:90));
  let g=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(aria)}">`;
  rows.forEach((r,i)=>{const y=i*RH+26;g+=`<text x="0" y="${y+5}" style="fill:var(--ink-2);font-size:${FS}px">${esc(r.l.length>MX?r.l.slice(0,MX-1)+'…':r.l)}</text>`;
   if(r.c.v==null){g+=`<text x="${LW}" y="${y+5}" style="font-size:14px">Muestra insuficiente</text>`;return;}
   g+=`<line x1="${X(lo)}" x2="${X(r.c.v)}" y1="${y}" y2="${y}" stroke="var(--line)" stroke-width="2"/><line x1="${X(r.c.lo??r.c.v)}" x2="${X(r.c.hi??r.c.v)}" y1="${y}" y2="${y}" stroke="var(--informal)" stroke-width="5" opacity=".3"/><circle cx="${X(r.c.v)}" cy="${y}" r="7" fill="var(--informal)"/><text x="${X(r.c.hi??r.c.v)+14}" y="${y+5}" style="fill:var(--ink);font-size:${FS}px">${esc(fmt(r.c.v,u))}${r.c.g==='B'?' (B)':''}</text>`;});
  return g+'</svg>';}
const NOTE='La barra clara es el intervalo de confianza de 95%. (B) marca una estimación menos precisa.';
function quienes(){const rows=D.domains[dom].groups.map(c=>({l:c.label,c})).sort((x,y)=>(y.c.v??-1e9)-(x.c.v??-1e9));
  el.innerHTML=`${chips(Object.entries(D.domains).map(([k,d])=>[k,d.label]),dom)}${dots(rows,'Valores por grupo')}<p class="r-src">${D.year}. ${NOTE}</p>`;
  el.querySelectorAll('.r-chips button').forEach(x=>x.onclick=()=>{dom=x.dataset.k;quienes();});}
function reparto(){const rows=D.national.map(c=>({l:c.label,c:c.cells[yi]}));
  el.innerHTML=`${chips(D.years.map((y,k)=>[k,y]).slice(-6),yi)}${dots(rows,'Reparto de los ocupados por categoría')}<p class="r-src">${D.years[yi]}. Porcentaje de los ocupados. ${NOTE}</p>`;
  el.querySelectorAll('.r-chips button').forEach(x=>x.onclick=()=>{yi=+x.dataset.k;reparto();});}
function datos(){
  const head=DIST?['categoria','anio']:['anio'],cols=['valor','error_estandar','ic95_inf','ic95_sup','n','sello'];
  const list=DIST?D.national.flatMap(c=>D.years.map((y,i)=>[c.label,y,c.cells[i]])):D.years.map((y,i)=>[y,D.national[i]]);
  const rows=[[...head,...cols],...list.map(r=>{const c=r.at(-1);return [...r.slice(0,-1),c.v,c.se,c.lo,c.hi,c.n,c.g];})];
  const show=DIST?list.filter(r=>r[1]===D.years[yi]):list;
  el.innerHTML=`${DIST?`${chips(D.years.map((y,k)=>[k,y]).slice(-6),yi)}`:''}<div class="r-scroll"><table class="r-table"><thead><tr><th>${DIST?'Categoría':'Año'}</th><th>Valor</th><th>Error est.</th><th>IC 95%</th><th>n</th><th>Sello</th></tr></thead><tbody>${show.map(r=>{const c=r.at(-1);return `<tr><td>${esc(r[0])}</td><td>${fmt(c.v,u)}</td><td>${c.se??''}</td><td>${c.v==null?'':fmt(c.lo,u)+' a '+fmt(c.hi,u)}</td><td>${c.n.toLocaleString('en-US')}</td><td>${c.g}</td></tr>`;}).join('')}</tbody></table></div>
<div class="r-actions"><button class="r-btn" id="csv">Descargar esta serie (CSV)</button></div><p class="r-src">Serie nacional${DIST?' de todas las categorías y años':''}. Por grupo y departamento, usa el archivo completo del indicador${D.explore?` o <a href="/explorar/?i=${id}">Explorar</a>`:''}.</p>`;
  el.querySelector('#csv').onclick=()=>download(`olp_${id}.csv`,csvRows(rows));
  if(DIST)el.querySelectorAll('.r-chips button').forEach(x=>x.onclick=()=>{yi=+x.dataset.k;datos();});}
const VIEW={tendencia,mapa,quienes,reparto,datos};
function show(t){if(!VIEW[t]||!TABS.some(x=>x[0]===t))t=TABS[0][0];elT.innerHTML=TABS.map(x=>`<button role="tab" aria-selected="${x[0]===t}" data-t="${x[0]}">${x[1]}</button>`).join('');elT.querySelectorAll('button').forEach(x=>x.onclick=()=>{history.replaceState(null,'','#'+x.dataset.t);show(x.dataset.t);});tip().hidden=true;VIEW[t]();}
show(location.hash.slice(1));
document.querySelectorAll('[data-copy]').forEach(x=>x.onclick=()=>copyText(x,document.getElementById(x.dataset.copy).textContent,'Copiado'));
