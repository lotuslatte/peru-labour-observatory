// Province page: map, relation between indicators, gaps within departments, typologies.
import {geoMercator,geoPath,scaleLinear,scaleQuantile,scaleSqrt,quantile} from 'd3';
import {feature,mesh} from 'topojson-client';
import {fmt,esc,CATS,tip,showTip,csvRows,download} from './olp.js';

const TABS=[['mapa','Mapa'],['relacion','Relación'],['brechas','Brechas'],['tipos','Tipologías']];
const W=560,H=640,METRO={type:'MultiPoint',coordinates:[[-77.35,-12.42],[-76.55,-11.72]]},INSET={x:16,y:452,s:150};
const elTabs=document.getElementById('tabs'),el=document.getElementById('view');
const S={tab:'mapa',ind:'informality',view:'valor',dept:'',sel:'',x:'informality',y:'median_inc_real'};
let A,T,prov,edges,coast,byId,dims,dept={};

const unit=d=>{const u=d.unit||'%';return u.startsWith('S')?'S/':u==='pp'?'pp':u==='h'?'h':'%';};
const dim=id=>dims.find(d=>d.id===id);
const cell=(r,id)=>r.values[id]||{v:null,g:'S'};
const small=()=>innerWidth<640;
const opts=(sel)=>dims.map(d=>`<option value="${d.id}"${d.id===sel?' selected':''}>${esc(d.label_es)}</option>`).join('');
const nat=id=>A.national[id]?.v;

function state(){const q=new URLSearchParams();q.set('i',S.ind);if(S.view!=='valor')q.set('v',S.view);if(S.dept)q.set('d',S.dept);if(S.sel)q.set('p',S.sel);if(S.tab==='relacion'){q.set('x',S.x);q.set('y',S.y);}history.replaceState(null,'',`?${q}#${S.tab}`);}
function parse(){const q=new URLSearchParams(location.search),t=location.hash.slice(1);if(TABS.some(x=>x[0]===t))S.tab=t;if(dim(q.get('i')))S.ind=q.get('i');if(q.get('v')==='peru')S.view='peru';if(dept[q.get('d')])S.dept=q.get('d');if(byId[q.get('p')])S.sel=q.get('p');if(dim(q.get('x')))S.x=q.get('x');if(dim(q.get('y')))S.y=q.get('y');}

// Comparison classes: only a 95% interval that excludes the national value counts as different.
function versus(c,id){const n=nat(id);if(c.v==null||n==null)return null;if(!c.se||c.lo==null)return 0;return c.lo>n?1:c.hi<n?-1:0;}
function painter(id){
  const rows=A.regions.map(r=>cell(r,id)).filter(c=>c.v!=null);
  if(S.view==='peru'){const far=quantile(rows.map(c=>Math.abs(c.v-nat(id))).sort((a,b)=>a-b),.5);
    return {fill:c=>{const k=versus(c,id);if(k==null)return 'url(#r-hatch)';if(k===0)return 'var(--div-4)';const strong=Math.abs(c.v-nat(id))>=far;return k>0?(strong?'var(--div-7)':'var(--div-6)'):(strong?'var(--div-1)':'var(--div-2)');}};}
  const s=scaleQuantile().domain(rows.map(c=>c.v)).range([1,2,3,4,5,6]);
  return {fill:c=>c.v==null?'url(#r-hatch)':`var(--seq-${s(c.v)})`,cuts:s.quantiles(),lo:Math.min(...rows.map(c=>c.v))};
}
const hatch=`<defs><pattern id="r-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="var(--panel-2)"/><line x1="0" y1="0" x2="0" y2="6" stroke="var(--muted)" stroke-width="1"/></pattern></defs>`;

function geoSvg(fillOf,label){
  const scope=S.dept?prov.features.filter(f=>f.properties.id.slice(0,2)===S.dept):prov.features;
  const fc={type:'FeatureCollection',features:scope},main=geoPath(geoMercator().fitExtent([[10,10],[W-10,H-10]],fc)).digits(1);
  const shape=(f,p)=>{const id=f.properties.id;return `<path class="p${id===S.sel?' on':''}" data-id="${id}" d="${p(f)}" fill="${fillOf(byId[id])}"/>`;};
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">${hatch}${scope.map(f=>shape(f,main)).join('')}`;
  if(!S.dept){const z=geoPath(geoMercator().fitExtent([[INSET.x,INSET.y],[INSET.x+INSET.s,INSET.y+INSET.s]],METRO)).digits(1),near=prov.features.filter(f=>['15','07'].includes(f.properties.id.slice(0,2)));
    s+=`<path class="b" d="${main(edges)}"/><path class="c" d="${main(coast)}"/><clipPath id="r-metro"><rect x="${INSET.x}" y="${INSET.y}" width="${INSET.s}" height="${INSET.s}"/></clipPath><rect class="r-inset" x="${INSET.x}" y="${INSET.y}" width="${INSET.s}" height="${INSET.s}"/><g clip-path="url(#r-metro)">${near.map(f=>shape(f,z)).join('')}</g><text class="r-inset-t" x="${INSET.x}" y="${INSET.y-8}">Lima y Callao</text>`;}
  return s+'</svg>';
}
function bindMap(root,tipHtml){root.querySelectorAll('path.p').forEach(p=>{const r=byId[p.dataset.id];
  p.onpointermove=e=>showTip(e,tipHtml(r));p.onpointerleave=()=>tip().hidden=true;
  p.onclick=()=>{tip().hidden=true;S.sel=r.id;if(!S.dept)S.dept=r.parent;render();};});}

function legend(pt,d,u){
  if(S.view==='peru'){const items=[['--div-1','Muy por debajo'],['--div-2','Por debajo'],['--div-4','Sin diferencia clara'],['--div-6','Por encima'],['--div-7','Muy por encima']];
    return `<div class="r-keys">${items.map(([c,l])=>`<span><i style="background:var(${c})"></i>${l}</span>`).join('')}<span><i class="h"></i>Sin dato</span></div><p class="r-src">Comparado con ${esc(fmt(nat(d.id),u))}, el valor nacional ${A.years[0]}–${A.years.at(-1)}. «Por encima» o «por debajo» exigen que el intervalo de 95% excluya ese valor; «muy» marca la mitad más alejada. ${d.higher_better?'Más alto es mejor.':'Más bajo es mejor.'}</p>`;}
  return `<div class="r-scale">${[pt.lo,...pt.cuts].map((v,i)=>`<span><i style="background:var(--seq-${i+1})"></i>${esc(fmt(v,u))}</span>`).join('')}</div><p class="r-src">(B) marca una estimación menos precisa. Cada tono parte del valor indicado y agrupa igual número de provincias. Más oscuro: valor más alto. ${d.higher_better?'Más alto es mejor.':'Más bajo es mejor.'}</p>`;
}
function detail(r,d,u){const c=cell(r,d.id),k=versus(c,d.id),rk=A.regions.filter(x=>cell(x,d.id).v!=null).sort((a,b)=>cell(b,d.id).v-cell(a,d.id).v).findIndex(x=>x.id===r.id)+1,tot=A.regions.filter(x=>cell(x,d.id).v!=null).length;
  const vs=k==null?'':k===0?`No se distingue del valor nacional (${esc(fmt(nat(d.id),u))}).`:`${k>0?'Por encima':'Por debajo'} del valor nacional (${esc(fmt(nat(d.id),u))}).`;
  return `<p class="r-rank-t">${esc(r.name)}</p><p class="r-src">${esc(r.dept_name)}</p><p class="r-pn">${c.v==null?'Sin dato':esc(fmt(c.v,u))}</p>${c.v==null?'<p class="r-src">La muestra no alcanza para publicar esta cifra.</p>':`<p class="r-src">IC 95%: ${esc(fmt(c.lo,u))} a ${esc(fmt(c.hi,u))}. ${c.n.toLocaleString('en-US')} personas en la muestra. Sello ${c.g}. Puesto ${rk} de ${tot}, de mayor a menor.</p><p>${vs}</p>`}<button class="r-btn" id="clear">Volver a la lista</button>`;}

function mapa(){const d=dim(S.ind),u=unit(d),pt=painter(d.id),rows=A.regions.filter(r=>(!S.dept||r.parent===S.dept)&&cell(r,d.id).v!=null).sort((a,b)=>cell(b,d.id).v-cell(a,d.id).v);
  const blanks=A.regions.length-A.regions.filter(r=>cell(r,d.id).v!=null).length,li=a=>a.map(r=>`<li><button data-p="${r.id}">${esc(r.name)}</button><span>${esc(fmt(cell(r,d.id).v,u))}${cell(r,d.id).g==='B'?' <span class="r-grade">(B)</span>':''}</span></li>`).join('');
  const counts=S.view==='peru'?A.regions.reduce((o,r)=>{const k=versus(cell(r,d.id),d.id);if(k!=null)o[k]=(o[k]||0)+1;return o;},{}):null;
  const list=S.dept?`<p class="r-rank-t">${esc(dept[S.dept])}</p><ul class="r-rank">${li(rows)}</ul>`:`<p class="r-rank-t">Más alto</p><ul class="r-rank">${li(rows.slice(0,5))}</ul><p class="r-rank-t">Más bajo</p><ul class="r-rank">${li(rows.slice(-5))}</ul>`;
  const sel=S.sel&&byId[S.sel];
  el.innerHTML=`<div class="r-ctl"><label>Indicador<select id="ind">${opts(d.id)}</select></label><label>Departamento<select id="dept"><option value="">Todo el Perú</option>${Object.entries(dept).sort((a,b)=>a[1].localeCompare(b[1],'es')).map(([k,v])=>`<option value="${k}"${k===S.dept?' selected':''}>${esc(v)}</option>`).join('')}</select></label><label>Buscar provincia<input id="find" type="search" list="provs" placeholder="Ej. Chota"><datalist id="provs">${A.regions.map(r=>`<option value="${esc(r.name)} (${esc(r.dept_name)})">`).join('')}</datalist></label></div>
<div class="r-chips"><button data-v="valor" aria-pressed="${S.view==='valor'}">Valor</button><button data-v="peru" aria-pressed="${S.view==='peru'}">Frente al Perú</button></div>
${blanks?`<p class="r-break">${A.regions.length-blanks} de ${A.regions.length} provincias tienen dato en este indicador.</p>`:''}
${counts?`<p class="r-src">${counts[1]||0} provincias por encima, ${counts[-1]||0} por debajo y ${counts[0]||0} sin diferencia clara. Con ${A.regions.length} comparaciones, unas 10 pueden salir distintas por azar.</p>`:''}
<div class="r-map"><div>${geoSvg(r=>pt.fill(cell(r,d.id)),`Mapa provincial de ${d.label_es}`)}${legend(pt,d,u)}</div><div>${sel?detail(sel,d,u):list}${S.dept?'<button class="r-btn" id="all">Ver todo el Perú</button>':''}</div></div>
<div class="r-actions"><button class="r-btn" id="csv">Descargar CSV de este indicador</button></div>`;
  bindMap(el,r=>{const c=cell(r,d.id);return `<b>${esc(r.name)}</b><br>${esc(r.dept_name)}<br>${c.v==null?'Sin dato':esc(fmt(c.v,u))}${c.lo!=null?`<br>IC ${esc(fmt(c.lo,u))} a ${esc(fmt(c.hi,u))}`:''}`;});
  el.querySelector('#ind').onchange=e=>{S.ind=e.target.value;render();};
  el.querySelector('#dept').onchange=e=>{S.dept=e.target.value;S.sel='';render();};
  el.querySelector('#find').onchange=e=>{const r=A.regions.find(x=>`${x.name} (${x.dept_name})`===e.target.value);if(r){S.sel=r.id;S.dept=r.parent;render();}};
  el.querySelectorAll('[data-v]').forEach(b=>b.onclick=()=>{S.view=b.dataset.v;render();});
  el.querySelectorAll('[data-p]').forEach(b=>b.onclick=()=>{S.sel=b.dataset.p;S.dept=byId[S.sel].parent;render();});
  const c=el.querySelector('#clear');if(c)c.onclick=()=>{S.sel='';render();};
  const all=el.querySelector('#all');if(all)all.onclick=()=>{S.dept='';S.sel='';render();};
  el.querySelector('#csv').onclick=()=>download(`olp_provincias_${d.id}.csv`,csvRows([['ubigeo','provincia','departamento','valor','error_estandar','ic95_inf','ic95_sup','n','sello'],...A.regions.map(r=>{const c=cell(r,d.id);return [r.id,r.name,r.dept_name,c.v,c.se,c.lo,c.hi,c.n,c.g];})]));
}

function weighted(rows){const w=rows.map(p=>T.pop[p.r.id]??1),s=w.reduce((a,b)=>a+b,0),mx=rows.reduce((a,r,i)=>a+w[i]*r.a,0)/s,my=rows.reduce((a,r,i)=>a+w[i]*r.b,0)/s;let c=0,vx=0,vy=0;rows.forEach((r,i)=>{c+=w[i]*(r.a-mx)*(r.b-my);vx+=w[i]*(r.a-mx)**2;vy+=w[i]*(r.b-my)**2;});return c/Math.sqrt(vx*vy);}
function relacion(){const dx=dim(S.x),dy=dim(S.y),ux=unit(dx),uy=unit(dy),rows=A.regions.map(r=>({r,a:cell(r,S.x).v,b:cell(r,S.y).v,t:T.typologies.province[r.id]})).filter(p=>p.a!=null&&p.b!=null);
  const P=small(),WS=P?380:920,HS=P?400:520,m={t:16,r:16,b:48,l:P?52:64},ext=f=>[Math.min(...rows.map(f)),Math.max(...rows.map(f))],x=scaleLinear().domain(ext(p=>p.a)).nice().range([m.l,WS-m.r]),y=scaleLinear().domain(ext(p=>p.b)).nice().range([HS-m.b,m.t]),rad=scaleSqrt().domain([0,Math.max(...Object.values(T.pop))]).range([0,P?16:26]);
  const lab=(t,u)=>esc(fmt(t,u).replace('.0%','%').replace('.0 ',' '));
  let s=`<svg viewBox="0 0 ${WS} ${HS}" role="img" aria-label="Relación entre ${esc(dx.label_es)} y ${esc(dy.label_es)}">`;
  y.ticks(6).forEach(t=>s+=`<line x1="${m.l}" x2="${WS-m.r}" y1="${y(t)}" y2="${y(t)}" stroke="var(--line)"/><text x="${m.l-8}" y="${y(t)+4}" text-anchor="end">${lab(t,uy)}</text>`);
  x.ticks(P?5:8).forEach(t=>s+=`<text x="${x(t)}" y="${HS-m.b+18}" text-anchor="middle">${lab(t,ux)}</text>`);
  if(nat(S.x)!=null)s+=`<line x1="${x(nat(S.x))}" x2="${x(nat(S.x))}" y1="${m.t}" y2="${HS-m.b}" stroke="var(--muted)" stroke-dasharray="4 4"/>`;
  if(nat(S.y)!=null)s+=`<line x1="${m.l}" x2="${WS-m.r}" y1="${y(nat(S.y))}" y2="${y(nat(S.y))}" stroke="var(--muted)" stroke-dasharray="4 4"/><text x="${WS-m.r}" y="${y(nat(S.y))-6}" text-anchor="end">Perú</text>`;
  [...rows].sort((a,b)=>T.pop[b.r.id]-T.pop[a.r.id]).forEach(p=>{s+=`<circle class="pt" data-id="${p.r.id}" cx="${x(p.a).toFixed(1)}" cy="${y(p.b).toFixed(1)}" r="${Math.max(3,rad(T.pop[p.r.id])).toFixed(1)}" fill="${p.t==null?'var(--panel-2)':`var(${CATS[p.t]})`}" fill-opacity=".72" stroke="var(--bg)"/>`;});
  s+='</svg>';
  const r=weighted(rows),plain=weighted(rows.map(p=>({...p,r:{id:'_'}})));
  el.innerHTML=`<div class="r-ctl"><label>Eje horizontal<select id="x">${opts(S.x)}</select></label><label>Eje vertical<select id="y">${opts(S.y)}</select></label></div>
<p class="r-say">Correlación de ${r.toFixed(2).replace('-','−')} entre las ${rows.length} provincias con ambos datos, ponderada por población (${plain.toFixed(2).replace('-','−')} sin ponderar).</p><p class="r-src">Es una asociación entre territorios, no una causa, y no dice nada de las personas dentro de cada provincia.${A.regions.length-rows.length?` ${A.regions.length-rows.length===1?'1 provincia queda':`${A.regions.length-rows.length} provincias quedan`} fuera por no tener alguna de las dos cifras.`:''}</p>
${s}<p class="r-src">Cada punto es una provincia y su tamaño, la población del censo 2017. El color es su tipología. Las líneas punteadas marcan el valor nacional.</p>${groupKeys()}`;
  el.querySelectorAll('.pt').forEach(c=>{const p=rows.find(q=>q.r.id===c.dataset.id);c.onpointermove=e=>showTip(e,`<b>${esc(p.r.name)}</b><br>${esc(p.r.dept_name)}<br>${esc(dx.label_es)}: ${esc(fmt(p.a,ux))}<br>${esc(dy.label_es)}: ${esc(fmt(p.b,uy))}`);c.onpointerleave=()=>tip().hidden=true;});
  el.querySelector('#x').onchange=e=>{S.x=e.target.value;render();};el.querySelector('#y').onchange=e=>{S.y=e.target.value;render();};
}

function brechas(){const d=dim(S.ind),u=unit(d),rows=T.gaps[d.id],P=small(),WS=P?380:920,LW=P?104:150,RW=P?62:84,RH=34;
  if(!rows.length){el.innerHTML='<p class="r-src">Sin datos para este indicador.</p>';return;}
  const vs=rows.flatMap(g=>[g.min.lo??g.min.v,g.max.hi??g.max.v]),x=scaleLinear().domain([Math.min(...vs),Math.max(...vs)]).nice().range([LW,WS-RW]),HS=rows.length*RH+30,clear=rows.filter(g=>g.clear).length,top=rows[0],rangeLab=g=>esc(u==='S/'?fmt(g.range,u):`${g.range.toFixed(1)} pp`);
  let s=`<svg viewBox="0 0 ${WS} ${HS}" role="img" aria-label="Brechas entre provincias por departamento">`;
  x.ticks(P?4:7).forEach(t=>s+=`<line x1="${x(t)}" x2="${x(t)}" y1="20" y2="${HS}" stroke="var(--line)"/><text x="${x(t)}" y="13" text-anchor="middle">${esc(fmt(t,u).replace('.0%','%').replace('.0 ',' '))}</text>`);
  rows.forEach((g,i)=>{const yy=30+i*RH+10,tone=g.clear?'var(--ink-2)':'var(--rule)';
    s+=`<g class="gp" data-i="${i}"><rect x="0" y="${yy-16}" width="${WS}" height="${RH}" fill="transparent"/><text x="${LW-10}" y="${yy+4}" text-anchor="end" style="fill:var(--ink)">${esc(dept[g.dept])}</text><line x1="${x(g.min.v)}" x2="${x(g.max.v)}" y1="${yy}" y2="${yy}" stroke="${tone}" stroke-width="2"/><circle cx="${x(g.min.v)}" cy="${yy}" r="5" fill="var(--cat-1)" stroke="var(--bg)" stroke-width="2"/><circle cx="${x(g.max.v)}" cy="${yy}" r="5" fill="var(--cat-2)" stroke="var(--bg)" stroke-width="2"/><text x="${WS-4}" y="${yy+4}" text-anchor="end">${rangeLab(g)}</text></g>`;});
  el.innerHTML=`<div class="r-ctl"><label>Indicador<select id="ind">${opts(d.id)}</select></label></div>
<p class="r-say">La mayor distancia está en ${esc(dept[top.dept])}: ${esc(top.min.name)} tiene ${esc(fmt(top.min.v,u))} y ${esc(top.max.name)}, ${esc(fmt(top.max.v,u))}.</p>
<p class="r-src">Para cada departamento con 3 o más provincias, el punto terracota es la provincia más baja y el azul, la más alta. En ${clear} de ${rows.length} departamentos los intervalos de ambas no se tocan; en los demás la línea va clara, porque la distancia podría ser ruido de muestra.</p><div class="r-scroll">${s}</svg></div>`;
  el.querySelectorAll('.gp').forEach(n=>{const g=rows[+n.dataset.i],line=e=>`${esc(e.name)}: ${esc(fmt(e.v,u))} (IC ${esc(fmt(e.lo,u))} a ${esc(fmt(e.hi,u))})`;n.onpointermove=e=>showTip(e,`<b>${esc(dept[g.dept])}</b><br>${line(g.min)}<br>${line(g.max)}`);n.onpointerleave=()=>tip().hidden=true;});
  el.querySelector('#ind').onchange=e=>{S.ind=e.target.value;render();};
}

const groupKeys=()=>`<div class="r-keys">${T.typologies.groups.map(g=>`<span><i style="background:var(${CATS[g.id]})"></i>${esc(g.name)}</span>`).join('')}</div>`;
function tipos(){const Y=T.typologies,gs=[...Y.groups].sort((a,b)=>b.pop_share-a.pop_share),saved=[S.dept,S.sel];S.dept='';S.sel='';
  const svg=geoSvg(r=>{const t=Y.province[r.id];return t==null?'url(#r-hatch)':`var(${CATS[t]})`;},'Mapa de tipologías provinciales');[S.dept,S.sel]=saved;
  const sp=Object.entries(T.spatial);
  el.innerHTML=`<p class="r-say">${Y.k} perfiles de mercado laboral. Son una forma de ordenar provincias parecidas, no tipos naturales: las fronteras entre grupos son difusas.</p>
<div class="r-map"><div>${svg}${groupKeys()}</div><div>${gs.map(g=>`<div class="r-group"><p class="r-rank-t"><i style="background:var(${CATS[g.id]})"></i>${esc(g.name)}</p><p class="r-src">${g.n} provincias, ${g.pop_share.toFixed(1)}% de la población. Empleo informal ${g.mean.informality.toFixed(1)}%, ingreso mediano S/${Math.round(g.mean.median_inc_real).toLocaleString('en-US')}, con seguro ${g.mean.seguro.toFixed(1)}%. Ej.: ${g.examples.slice(0,3).map(esc).join(', ')}.</p></div>`).join('')}</div></div>
<div class="r-actions"><button class="r-btn" id="csv">Descargar CSV de tipologías</button></div>
<details class="r-details"><summary>Método de las tipologías</summary><p>K-medias sobre ${Y.dims.length} indicadores estandarizados: ${Y.dims.map(i=>esc(dim(i).label_es.toLowerCase())).join(', ')}. Se eligió ${Y.k} grupos por silueta (${Y.silhouette[Y.k].toFixed(2)}, un valor bajo que indica grupos solapados). Al remuestrear provincias, la asignación se mantiene con un índice de Rand ajustado de ${Y.stability_ari.toFixed(2)}. Sin la informalidad, que agrupa dos métodos de medición, el índice es ${Y.ari_without_informality.toFixed(2)}, así que esa mezcla no define los grupos. Los promedios se ponderan por población del censo 2017 y son aproximados. ${Y.excluded===1?'1 provincia queda':`${Y.excluded} provincias quedan`} sin tipo por falta de datos.</p></details>
<details class="r-details"><summary>¿Se agrupan en el territorio?</summary><p>Sí, de forma moderada: las provincias vecinas se parecen más de lo esperado por azar en los ${sp.length} indicadores revisados, pero pocas zonas destacan por sí solas. I de Moran con contigüidad de frontera y ${(9999).toLocaleString('en-US')} permutaciones; zonas locales con corrección de falsos descubrimientos al 5%.</p>
<div class="r-scroll"><table class="r-table"><thead><tr><th>Indicador</th><th>I de Moran</th><th>Zonas locales</th></tr></thead><tbody>${sp.map(([id,s])=>`<tr><td>${esc(dim(id).label_es)}</td><td>${s.moran_i.toFixed(2)}</td><td>${Object.keys(s.cluster).length}</td></tr>`).join('')}</tbody></table></div></details>`;
  bindMap(el,r=>{const t=Y.province[r.id];return `<b>${esc(r.name)}</b><br>${esc(r.dept_name)}<br>${t==null?'Sin tipología':esc(Y.groups[t].name)}`;});
  el.querySelectorAll('path.p').forEach(p=>p.onclick=null);
  el.querySelector('#csv').onclick=()=>download('olp_provincias_tipologias.csv',csvRows([['ubigeo','provincia','departamento','tipologia'],...A.regions.map(r=>[r.id,r.name,r.dept_name,Y.province[r.id]==null?'':Y.groups[Y.province[r.id]].name])]));
}

const VIEW={mapa,relacion,brechas,tipos};
function render(){elTabs.innerHTML=TABS.map(([k,l])=>`<button role="tab" aria-selected="${k===S.tab}" data-t="${k}">${l}</button>`).join('');elTabs.querySelectorAll('button').forEach(b=>b.onclick=()=>{S.tab=b.dataset.t;render();});tip().hidden=true;state();VIEW[S.tab]();}

Promise.all(['atlas_provincias.json','territorios.json','provincias.topo.json','departamentos.topo.json'].map(f=>fetch(`/data/${f}`).then(r=>{if(!r.ok)throw new Error(f);return r.json();}))).then(([a,t,pt,dt])=>{
  A=a;T=t;dims=a.dims;byId=Object.fromEntries(a.regions.map(r=>[r.id,r]));a.regions.forEach(r=>dept[r.parent]=r.dept_name);
  prov=feature(pt,pt.objects.data);edges=mesh(dt,dt.objects.data,(x,y)=>x!==y);coast=mesh(dt,dt.objects.data,(x,y)=>x===y);
  parse();render();addEventListener('hashchange',()=>{parse();render();});addEventListener('resize',()=>{if(S.tab==='relacion'||S.tab==='brechas')render();});
}).catch(e=>{console.error(e);el.innerHTML='<p class="r-src">No se pudieron cargar los datos. Intenta de nuevo o descárgalos en <a href="/datos/">Datos</a>.</p>';});
