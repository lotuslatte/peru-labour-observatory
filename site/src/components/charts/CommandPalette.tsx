import { useEffect, useState, useRef } from 'preact/hooks';
interface Item { label: string; href: string; group: string }
export default function CommandPalette({ regions }: { regions: { id: string; name: string }[] }) {
  const [open, setOpen] = useState(false); const [q, setQ] = useState(''); const [i, setI] = useState(0);
  const input = useRef<HTMLInputElement>(null); const box = useRef<HTMLDivElement>(null); const opener = useRef<HTMLElement | null>(null);
  const items: Item[] = [
    { label: 'Inicio', href: '/', group: 'Páginas' }, { label: 'Atlas de capacidades', href: '/atlas/', group: 'Páginas' },
    { label: 'Historias', href: '/historias/', group: 'Páginas' }, { label: 'Compendio estadístico', href: '/compendio/', group: 'Páginas' },
    { label: 'Atlas provincial', href: '/atlas/provincias/', group: 'Páginas' }, { label: 'Análisis con controles', href: '/analisis/', group: 'Páginas' },
    { label: 'Novedades: qué cambió', href: '/novedades/', group: 'Páginas' }, { label: 'Validación frente a INEI', href: '/acerca/validacion/', group: 'Páginas' },
    { label: 'Glosario', href: '/glosario/', group: 'Páginas' }, { label: 'Preguntas frecuentes', href: '/preguntas/', group: 'Páginas' },
    { label: 'Metodología', href: '/acerca/metodologia/', group: 'Páginas' }, { label: 'Escuela de encuestas', href: '/acerca/escuela-de-encuestas/', group: 'Páginas' },
    { label: 'Descargar datos', href: '/datos/', group: 'Páginas' }, { label: 'Acerca del Observatorio', href: '/acerca/', group: 'Páginas' },
    ...regions.map(r => ({ label: r.name, href: `/atlas/${r.id}/`, group: 'Departamentos' })),
  ];
  const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const res = items.filter(it => norm(it.label).includes(norm(q))).slice(0, 12);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setOpen(o => !o); }
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKey);
    document.querySelectorAll('[data-open-palette]').forEach(b => b.addEventListener('click', () => setOpen(true)));
    return () => window.removeEventListener('keydown', onKey);
  }, []);
  // Al abrir se recuerda quién tenía el foco y se devuelve al cerrar.
  useEffect(() => { if (open) { opener.current = document.activeElement as HTMLElement; setQ(''); setI(0); setTimeout(() => input.current?.focus(), 10); } else { opener.current?.focus?.(); opener.current = null; } }, [open]);
  const trap = (e: KeyboardEvent) => {
    if (e.key !== 'Tab' || !box.current) return;
    const f = Array.from(box.current.querySelectorAll<HTMLElement>('input, a[href]')); if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); } else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  };
  if (!open) return null;
  return (
    <div class="cp-back" onClick={() => setOpen(false)}>
      <div class="cp" ref={box} role="dialog" aria-modal="true" aria-label="Buscar" onClick={e => e.stopPropagation()} onKeyDown={trap}>
        <input ref={input} type="search" placeholder="Buscar departamento, página…" aria-label="Buscar departamento o página" value={q} onInput={e => { setQ((e.target as HTMLInputElement).value); setI(0); }}
          onKeyDown={e => { if (e.key === 'ArrowDown') setI(x => Math.min(x + 1, res.length - 1)); if (e.key === 'ArrowUp') setI(x => Math.max(x - 1, 0)); if (e.key === 'Enter' && res[i]) location.href = res[i].href; }} />
        <ul>{res.map((r, k) => <li class={k === i ? 'sel' : ''}><a href={r.href} aria-current={k === i ? 'true' : undefined}><span class="g">{r.group}</span>{r.label}</a></li>)}</ul>
      </div>
      <style>{`.cp-back{position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:100;display:flex;align-items:flex-start;justify-content:center;padding-top:12vh}
        .cp{width:min(560px,92vw);background:var(--panel);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);overflow:hidden}
        .cp input{width:100%;border:0;border-bottom:1px solid var(--line);border-radius:0;padding:14px 16px;font-size:1rem}
        .cp ul{list-style:none;margin:0;padding:6px;max-height:50vh;overflow:auto}.cp li a{display:flex;gap:10px;align-items:center;padding:8px 10px;border-radius:8px;text-decoration:none;color:var(--ink)}
        .cp li.sel a,.cp li a:hover{background:var(--panel-2)}.cp .g{font-family:var(--font-mono);font-size:.68rem;color:var(--muted);min-width:96px}`}</style>
    </div>
  );
}
