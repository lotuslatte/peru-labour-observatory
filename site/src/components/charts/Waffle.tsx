import { useEffect, useState } from 'preact/hooks';
// 100 personas: cada punto = 1 % de los ocupados. Firma visual del sitio.
export default function Waffle({ informal, label }: { informal: number; label?: string }) {
  const [shown, setShown] = useState(0);
  const n = Math.round(informal);
  useEffect(() => {
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) { setShown(100); return; }
    let i = 0; const id = setInterval(() => { i += 3; setShown(Math.min(i, 100)); if (i >= 100) clearInterval(id); }, 18);
    return () => clearInterval(id);
  }, []);
  return (
    <figure class="waffle" aria-label={`${n} de cada 100 ocupados tienen empleo informal`}>
      <div class="grid" role="img">{Array.from({ length: 100 }, (_, i) => <span class={`p ${i < n ? 'inf' : 'for'} ${i < shown ? 'on' : ''}`} style={{ transitionDelay: `${(i % 10) * 12}ms` }} />)}</div>
      <figcaption><span class="big">{n}</span> de cada <span class="big muted">100</span> personas ocupadas trabajan sin la protección de un empleo formal{label ? ` · ${label}` : ''}</figcaption>
      <style>{`.waffle{margin:0}.waffle .grid{display:grid;grid-template-columns:repeat(10,1fr);gap:6px;max-width:340px}
        .waffle .p{aspect-ratio:1;border-radius:50%;background:var(--panel-2);transform:scale(.4);opacity:.2;transition:transform .35s cubic-bezier(.2,.8,.2,1),opacity .35s}
        .waffle .p.on{transform:scale(1);opacity:1}.waffle .p.inf.on{background:var(--informal)}.waffle .p.for.on{background:var(--formal)}
        .waffle figcaption{margin-top:14px;font-family:var(--font-serif);font-size:1.15rem;line-height:1.35;max-width:340px;color:var(--ink-2)}
        .waffle .big{font-size:1.9rem;color:var(--informal);font-weight:500}.waffle .big.muted{color:var(--formal)}`}</style>
    </figure>
  );
}
