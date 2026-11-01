import {fmt,esc,CATS,findBreak,tip,lineChart,csvRows,copyText,download} from './olp.js';
let D,IDS,YRS;const hasBreak=id=>findBreak(D.breaks,id);
const G={national:'todo el Perú',sex:'sexo',area:'área',region_nat:'región natural',age4:'edad',educ4:'educación',lengua3:'lengua',etnia6:'etnia',dept:'un departamento'};
const S={ind:'informality',g:'sex',dept:'08',a:2014,b:9999};
const EX=[['Ingreso mediano por educación',{ind:'median_inc_real',g:'educ4'}],['Desempleo juvenil por sexo',{ind:'ur_youth',g:'sex'}],['Empleo informal en Cusco',{ind:'informality',g:'dept',dept:'08'}],['Seguro de salud por lengua',{ind:'seguro',g:'lengua3'}]];
const query=()=>{const q=new URLSearchParams({i:S.ind,g:S.g,a:S.a,b:S.b});if(S.g==='dept')q.set('d',S.dept);return '?'+q;};
function parse(){const q=new URLSearchParams(location.search);if(IDS.includes(q.get('i')))S.ind=q.get('i');if(G[q.get('g')])S.g=q.get('g');if(q.get('d'))S.dept=q.get('d');if(YRS.includes(+q.get('a')))S.a=+q.get('a');if(YRS.includes(+q.get('b')))S.b=+q.get('b');}
function deptOK(i){return !!D.series.dept[i];}
function series(){const yi=YRS.map((y,i)=>[y,i]).filter(([y])=>y>=S.a&&y<=S.b).map(x=>x[1]),pick=c=>yi.map(i=>c[i]),nat={label:'Perú',cells:pick(D.series.national[S.ind])};
  if(S.g==='national')return [{...nat,color:'--cat-1'}];
  if(S.g==='dept'){const r=D.regions.find(x=>x.id===S.dept);return [{label:r.name,cells:pick(D.series.dept[S.ind][S.dept]),color:'--cat-1'},{...nat,color:'--cat-6'}];}
  return Object.entries(D.series[S.g][S.ind]).map(([k,c],i)=>({label:D.labels[S.g][k],cells:pick(c),color:CATS[i]})).filter(s=>s.cells.some(c=>c.v!=null));}
function sel(id,opts,val){return `<select id="${id}" aria-label="${id}">${opts.map(([v,l,dis])=>`<option value="${v}" ${String(v)===String(val)?'selected':''} ${dis?'disabled':''}>${esc(l)}</option>`).join('')}</select>`;}
function render(){if(S.g==='dept'&&!deptOK(S.ind))S.g='national';if(S.ind==='gap_lfpr'&&S.g==='sex')S.g='national';
  const u=D.ind[S.ind].unit,yrs=YRS.filter(y=>y>=S.a&&y<=S.b),ss=series(),b=hasBreak(S.ind);
  const gs=Object.entries(G).map(([k,l])=>[k,k==='national'?l:(k==='dept'?l:'por '+l),(k==='dept'&&!deptOK(S.ind))||(S.ind==='gap_lfpr'&&k==='sex')]);
  document.getElementById('q').innerHTML=`Muéstrame ${sel('indicador',IDS.map(i=>[i,D.ind[i].label]),S.ind)} ${sel('grupo',gs,S.g)} ${S.g==='dept'?sel('departamento',D.regions.map(r=>[r.id,r.name]),S.dept):''} de ${sel('desde',YRS.filter(y=>y<S.b).map(y=>[y,y]),S.a)} a ${sel('hasta',YRS.filter(y=>y>S.a).map(y=>[y,y]),S.b)}`;
  for(const [id,k] of [['indicador','ind'],['grupo','g'],['departamento','dept'],['desde','a'],['hasta','b']]){const e=document.getElementById(id);if(e)e.onchange=()=>{S[k]=(k==='a'||k==='b')?+e.value:e.value;push();};}
  const lastY=yrs.at(-1),top=ss[0],c=top.cells.at(-1),crosses=b&&S.a<b.year&&S.b>=b.year;
  const ans=ss.length===1?`<b>${fmt(c.v,u)}</b> en ${lastY}`:ss.filter(s=>s.cells.at(-1).v!=null).sort((x,y)=>y.cells.at(-1).v-x.cells.at(-1).v).slice(0,1).map(s=>{const l=ss.filter(k=>k.cells.at(-1).v!=null).sort((x,y)=>x.cells.at(-1).v-y.cells.at(-1).v)[0];return `<b>${fmt(s.cells.at(-1).v,u)}</b> en ${esc(s.label)} y <b>${fmt(l.cells.at(-1).v,u)}</b> en ${esc(l.label)}, ${lastY}`;})[0]||'Sin datos publicables';
  const leg=ss.length>1?`<div class="r-legend">${ss.map(s=>`<span><i style="background:var(${s.color})"></i>${esc(s.label)}</span>`).join('')}</div>`:'';
  const head=['Grupo',...yrs],body=ss.map(s=>[s.label,...s.cells.map(c=>c.v)]);
  document.getElementById('res').innerHTML=`<p class="r-ans">${ans}</p><p class="r-src">ENAHO, INEI. ${esc(D.ind[S.ind].label)}.</p>${crosses?`<p class="r-break">${esc(b.label_es)}</p>`:''}${leg}<div id="ch"></div>
<section style="margin-top:32px"><div class="r-scroll"><table class="r-table"><thead><tr>${head.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${ss.map(s=>`<tr><td>${esc(s.label)}</td>${s.cells.map(c=>`<td>${fmt(c.v,u)}${c.g==='B'?' <span class="r-grade">B</span>':''}</td>`).join('')}</tr>`).join('')}</tbody></table></div>
<div class="r-actions"><button class="r-btn" id="csv">Descargar CSV</button><button class="r-btn" id="lnk">Copiar enlace</button></div><p class="r-src">Celda vacía: muestra insuficiente. B: estimación menos precisa. El CSV incluye error estándar, intervalo, n y sello.</p></section>`;
  const small=innerWidth<620;lineChart(document.getElementById('ch'),ss,yrs,u,crosses?b:null,{labels:!small&&ss.length<=4,band:ss.length===1,w:small?380:920,h:small?280:380,aria:D.ind[S.ind].label});
  document.getElementById('csv').onclick=()=>download(`olp_${S.ind}_${S.g}.csv`,csvRows([['indicador','grupo','anio','valor','error_estandar','ic95_inf','ic95_sup','n','sello'],...ss.flatMap(s=>s.cells.map((c,i)=>[S.ind,s.label,yrs[i],c.v,c.se,c.lo,c.hi,c.n,c.g]))]));
  document.getElementById('lnk').onclick=e=>copyText(e.target,location.href,'Enlace copiado');
  document.getElementById('try').innerHTML='Prueba: '+EX.map((x,i)=>`<button data-i="${i}">${x[0]}</button>`).join('');
  document.querySelectorAll('#try button').forEach(t=>t.onclick=()=>{Object.assign(S,EX[+t.dataset.i][1]);push();});}
function push(){history.replaceState(null,'',query());render();}
fetch('/data/explorar.json').then(r=>r.json()).then(j=>{D=j;IDS=Object.keys(D.ind);YRS=D.years;S.b=YRS.at(-1);parse();document.getElementById('q').className='r-q';render();}).catch(()=>{document.getElementById('res').innerHTML='<p class="r-src">No se pudieron cargar los datos. Recarga la página.</p>';});
