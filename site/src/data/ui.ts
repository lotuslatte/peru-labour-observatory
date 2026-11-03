// Plain-language names and definitions for the indicators with a public annual series.
import { feature, mesh } from 'topojson-client';
import { geoMercator, geoPath } from 'd3';
// The six signals on the home page come first, in display order.
import fs from 'node:fs';
import path from 'node:path';
import { YEAR } from './release';
export interface UiInd { id: string; name: string; what?: string; group: string; def: string; say?: (v: number, f: (x: number) => string) => string }
// Names, groups and definitions come from the pipeline (fichas/index.json); only the home-page wording lives here.
const DOCS: Record<string, { name: string; group: string; def: string }> = Object.fromEntries(JSON.parse(fs.readFileSync(path.resolve(process.cwd(), 'public/data/fichas/index.json'), 'utf8')).indicators.map((d: any) => [d.id, d]));
const LOCAL: { id: string; what?: string; say?: UiInd['say'] }[] = [
  { id: 'informality', what: 'de quienes trabajan, sin protección laboral', say: v => `De cada 100 personas ocupadas, ${Math.round(v)} tienen un empleo informal.` },
  { id: 'ur', what: 'de la fuerza laboral busca y no encuentra', say: v => `Cerca de ${Math.round(v)} de cada 100 personas que trabajan o buscan trabajo no encuentran empleo.` },
  { id: 'adecuado', what: 'de quienes trabajan, sin subempleo', say: v => `${Math.round(v)} de cada 100 ocupados no están subempleados por horas ni por ingresos.` },
  { id: 'lfpr', what: 'de mayores de 14 trabaja o busca trabajo', say: v => `${Math.round(v)} de cada 100 personas de 14 años a más trabajan o buscan trabajo.` },
  { id: 'median_inc_real', what: `al mes, en soles de ${YEAR}`, say: (_, f) => `La mitad de quienes reciben ingreso laboral gana menos de ${f(_)} al mes.` },
  { id: 'gap_lfpr', what: 'entre hombres y mujeres', say: v => `La actividad de los hombres supera a la de las mujeres en ${v.toFixed(1)} puntos.` },
  { id: 'epr' },
  { id: 'ur_youth' },
  { id: 'neet' },
  { id: 'subemp_hours' },
  { id: 'contract_any' },
  { id: 'pension' },
  { id: 'seguro' },
  { id: 'mean_inc_real' },
  { id: 'hours_mean' },
  { id: 'hours_le48' },
  { id: 'self_emp' },
  { id: 'tfnr' },
];
export const INDICATORS: UiInd[] = LOCAL.map(l => ({ ...l, name: DOCS[l.id].name, group: DOCS[l.id].group, def: DOCS[l.id].def }));
export const SIX = INDICATORS.filter(i => i.what);
export const UNITS: Record<string, string> = { median_inc_real: 'S/', mean_inc_real: 'S/', gap_lfpr: 'pp', hours_mean: 'h' };
export const unitOf = (id: string) => UNITS[id] ?? '%';
export const fmtU = (v: number, u: string) => u === '%' ? v.toFixed(1) + '%' : u === 'S/' ? 'S/' + Math.round(v).toLocaleString('en-US') : u === 'S/h' ? 'S/' + v.toFixed(2) + ' por hora' : u === 'ratio' ? v.toFixed(2) : `${v.toFixed(1)} ${u}`;
export const DOMAINS: Record<string, string> = { sex: 'Sexo', area: 'Área', region_nat: 'Región natural', age4: 'Edad', educ4: 'Educación', lengua3: 'Lengua', etnia6: 'Etnia' };
// Suppressed cells never reach the page with a value.
export const slim = (c: any) => c.g === 'S' || c.v == null ? { v: null, g: 'S', n: c.n ?? 0 } : { v: c.v, g: c.g, n: c.n, se: c.se, lo: c.lo, hi: c.hi };
/** Department outlines as SVG paths, decoded from the public topology. */
// Drawn from the shared-border topology. Never thin individual rings: neighbours stop matching.
export function peruMap() {
  const W = 560, H = 640, I = { x: 16, y: 452, s: 150 };
  const t = JSON.parse(fs.readFileSync(path.resolve(process.cwd(), 'public/data/departamentos.topo.json'), 'utf8'));
  const fc: any = feature(t, t.objects.data);
  const main = geoPath(geoMercator().fitExtent([[10, 10], [W - 10, H - 10]], fc)).digits(1);
  const metro = { type: 'MultiPoint', coordinates: [[-77.35, -12.42], [-76.55, -11.72]] };
  const zoom = geoPath(geoMercator().fitExtent([[I.x, I.y], [I.x + I.s, I.y + I.s]], metro as any)).digits(1);
  const paths = fc.features.map((f: any) => ({ id: f.properties.id, d: main(f) }));
  const inset = fc.features.filter((f: any) => ['07', '15'].includes(f.properties.id)).map((f: any) => ({ id: f.properties.id, d: zoom(f) }));
  const edge: any = mesh(t, t.objects.data, (a: any, b: any) => a === b);
  return { box: `0 0 ${W} ${H}`, paths, inset, I, outline: main(edge), insetOutline: zoom(edge) };
}
