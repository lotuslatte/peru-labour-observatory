// Search index for the palette: indicators, departments, provinces, pages and glossary terms.
import type { APIRoute } from 'astro';
import { loadAtlas, loadProvinces, loadIndex } from '../../data/loaders';
import { ALL_INDICATORS } from '../../data/ui';
import { NAV, FOOTER } from '../../data/site';

export const GET: APIRoute = () => {
  const pages = [...NAV, ...FOOTER.flatMap(c => c.links)].filter(([href], k, a) => a.findIndex(x => x[0] === href) === k);
  const slug = (t: string) => t.toLowerCase().replace(/\W+/g, '-');
  const items = [
    ...ALL_INDICATORS.map(i => ({ label: i.name, href: `/indicadores/${i.id}/`, group: 'Indicador', hint: `${i.group} ${i.def}` })),
    ...loadAtlas().regions.map(r => ({ label: r.name, href: `/atlas/${r.id}/`, group: 'Departamento' })),
    ...loadProvinces().regions.map((r: any) => ({ label: r.name, href: `/atlas/provincias/?p=${r.id}`, group: `Provincia de ${r.dept_name}` })),
    ...pages.map(([href, label]) => ({ label, href, group: 'Página' })),
    ...(loadIndex().glossary ?? []).map((g: any) => ({ label: g.term, href: `/glosario/#${slug(g.term)}`, group: 'Glosario', hint: g.def })),
  ];
  return new Response(JSON.stringify(items), { headers: { 'Content-Type': 'application/json' } });
};
