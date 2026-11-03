// Shared helpers for the indicator pages and the explorer: formatting, line chart, CSV.
const UNITS={'%':v=>v.toFixed(1)+'%','S/':v=>'S/'+Math.round(v).toLocaleString('en-US'),'pp':v=>v.toFixed(1)+' pp','h':v=>v.toFixed(1)+' h','S/h':v=>'S/'+v.toFixed(2),'ratio':v=>v.toFixed(2)};
const fmt=(v,u)=>v==null?'':UNITS[u](v);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const CATS=['--cat-1','--cat-2','--cat-4','--cat-3','--cat-5','--cat-9'];
function findBreak(breaks,id){return breaks.find(b=>b.indicators.includes(id));}
function tip(){let t=document.getElementById('tip');if(!t){t=document.createElement('div');t.id='tip';t.className='tip';t.hidden=true;document.body.append(t);}return t;}
function showTip(e,html){const t=tip();t.innerHTML=html;t.hidden=false;const x=Math.min(e.clientX+14,innerWidth-t.offsetWidth-8);t.style.left=x+'px';t.style.top=Math.max(8,e.clientY-t.offsetHeight-12)+'px';}
function ticks(lo,hi,n=5){const s=(hi-lo)/n,m=10**Math.floor(Math.log10(s)),st=[1,2,2.5,5,10].map(k=>k*m).find(k=>k>=s),o=[];for(let v=Math.ceil(lo/st)*st;v<=hi+1e-9;v+=st)o.push(+v.toFixed(6));return o;}
function segments(cells,years,brk){const out=[];let cur=[];cells.forEach((c,i)=>{if(c.v==null){if(cur.length)out.push(cur);cur=[];return;}if(brk&&years[i]===brk.year&&cur.length){out.push(cur);cur=[];}cur.push([years[i],c]);});if(cur.length)out.push(cur);return out;}
/* series: [{label,cells,color}] */
function lineChart(el,series,years,unit,brk,opts={}){
  const W=opts.w||920,H=opts.h||380,m={t:24,r:opts.labels?150:24,b:30,l:52};
  const all=series.flatMap(s=>s.cells.flatMap(c=>c.v==null?[]:[opts.band&&c.lo!=null?c.lo:c.v,opts.band&&c.hi!=null?c.hi:c.v]));
  if(!all.length){el.innerHTML='<p class="src">Sin datos publicables para esta selección.</p>';return;}
  let lo=Math.min(...all),hi=Math.max(...all);const p=(hi-lo)*.12||1;lo-=p;hi+=p;if(lo<0)lo=0;
  const tk=ticks(lo,hi),y0=Math.min(lo,tk[0]),y1=Math.max(hi,tk.at(-1));
  const X=y=>years.length>1?m.l+(y-years[0])/(years.at(-1)-years[0])*(W-m.l-m.r):m.l,Y=v=>H-m.b-(v-y0)/(y1-y0)*(H-m.t-m.b);
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opts.aria||'Serie anual')}">`;
  tk.forEach(t=>{s+=`<line x1="${m.l}" x2="${W-m.r}" y1="${Y(t)}" y2="${Y(t)}" stroke="var(--line)"/><text x="${m.l-8}" y="${Y(t)+4}" text-anchor="end">${esc(fmt(t,unit).replace('.0%','%').replace('.0 ',' '))}</text>`;});
  const step=years.length>8&&W<700?2:1;
  years.forEach((y,i)=>{if((years.length-1-i)%step===0)s+=`<text x="${X(y)}" y="${H-8}" text-anchor="middle">${y}</text>`;});
  if(brk&&brk.year>years[0]&&brk.year<=years.at(-1)){const bx=X(brk.year-.5);s+=`<line x1="${bx}" x2="${bx}" y1="${m.t-6}" y2="${H-m.b}" stroke="var(--warn)" stroke-dasharray="4 4"/><text x="${bx-6}" y="${m.t+4}" text-anchor="end" style="fill:var(--warn)">Cambio de método</text>`;}
  series.forEach(sr=>{segments(sr.cells,years,brk).forEach(seg=>{
    if(opts.band&&seg.length>1){const up=seg.map(([y,c])=>`${X(y)},${Y(c.hi)}`),dn=seg.map(([y,c])=>`${X(y)},${Y(c.lo)}`).reverse();s+=`<polygon points="${up.concat(dn).join(' ')}" fill="${`var(${sr.color})`}" opacity=".14"/>`;}
    if(seg.length>1)s+=`<polyline fill="none" stroke="var(${sr.color})" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round" points="${seg.map(([y,c])=>`${X(y)},${Y(c.v)}`).join(' ')}"/>`;
    else s+=`<circle cx="${X(seg[0][0])}" cy="${Y(seg[0][1].v)}" r="3.5" fill="var(${sr.color})"/>`;
  });});
  if(opts.labels){const items=series.map(sr=>{const i=sr.cells.map(c=>c.v!=null).lastIndexOf(true);return i<0?null:{l:sr.label,c:sr.color,x:X(years[i]),y:Y(sr.cells[i].v),v:sr.cells[i].v};}).filter(Boolean).sort((a,b)=>a.y-b.y);
    let prev=-99;items.forEach(it=>{const ly=Math.max(it.y+4,prev+16);prev=ly;const short=it.l.length>20?it.l.slice(0,19)+'…':it.l;s+=`<circle cx="${it.x}" cy="${it.y}" r="4" fill="var(${it.c})" stroke="var(--bg)" stroke-width="2"/><text x="${W-m.r+10}" y="${ly}" style="fill:var(--ink-2)">${esc(short)}</text>`;});}
  else series.forEach(sr=>{const i=sr.cells.map(c=>c.v!=null).lastIndexOf(true);if(i>=0)s+=`<circle cx="${X(years[i])}" cy="${Y(sr.cells[i].v)}" r="4.5" fill="var(${sr.color})" stroke="var(--bg)" stroke-width="2"/>`;});
  s+=`<line class="cross" y1="${m.t}" y2="${H-m.b}" stroke="var(--muted)" visibility="hidden"/><rect class="hit" x="${m.l}" y="0" width="${W-m.l-m.r}" height="${H}" fill="transparent"/></svg>`;
  el.innerHTML=s;const svg=el.querySelector('svg'),hit=svg.querySelector('.hit'),cross=svg.querySelector('.cross');
  hit.addEventListener('pointermove',e=>{const r=svg.getBoundingClientRect(),px=(e.clientX-r.left)/r.width*W;let i=0,b=1e9;years.forEach((y,k)=>{const d=Math.abs(X(y)-px);if(d<b){b=d;i=k;}});
    cross.setAttribute('x1',X(years[i]));cross.setAttribute('x2',X(years[i]));cross.setAttribute('visibility','visible');
    showTip(e,`<b>${years[i]}</b><br>`+series.map(sr=>{const c=sr.cells[i];return `${series.length>1?esc(sr.label)+': ':''}${c.v==null?'sin dato':esc(fmt(c.v,unit))}${c.lo!=null&&series.length==1?` (IC ${esc(fmt(c.lo,unit))} a ${esc(fmt(c.hi,unit))})`:''}`;}).join('<br>'));});
  hit.addEventListener('pointerleave',()=>{cross.setAttribute('visibility','hidden');tip().hidden=true;});
}
function csvRows(rows){return rows.map(r=>r.map(x=>{const t=x==null?'':String(x);return /[",\n]/.test(t)?'"'+t.replace(/"/g,'""')+'"':t;}).join(',')).join('\n');}
async function copyText(btn,text,ok){const old=btn.textContent;try{await navigator.clipboard.writeText(text);btn.textContent=ok;}catch(e){btn.textContent='No se pudo copiar';}setTimeout(()=>btn.textContent=old,1800);}
function download(name,text){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['\ufeff'+text],{type:'text/csv;charset=utf-8'}));a.download=name;a.click();URL.revokeObjectURL(a.href);}
export {fmt,esc,CATS,findBreak,tip,showTip,segments,lineChart,csvRows,copyText,download};
