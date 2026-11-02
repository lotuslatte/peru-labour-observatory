// Plain-language names and definitions for the indicators with a public annual series.
import { feature, mesh } from 'topojson-client';
import { geoMercator, geoPath } from 'd3';
// The six signals on the home page come first, in display order.
import fs from 'node:fs';
import path from 'node:path';
import { YEAR } from './release';
export interface UiInd { id: string; name: string; what?: string; group: string; def: string; say?: (v: number, f: (x: number) => string) => string }
export const INDICATORS: UiInd[] = [
  { id: 'informality', name: 'Empleo informal', what: 'de quienes trabajan, sin protección laboral', group: 'Calidad del empleo', say: v => `De cada 100 personas ocupadas, ${Math.round(v)} tienen un empleo informal.`, def: 'Ocupados en empleo informal entre el total de ocupados de 14 años a más. De 2014 a 2023 usa la variable ocupinf del INEI. Desde 2024 el INEI no la publica y se usa la regla del Observatorio.' },
  { id: 'ur', name: 'Desempleo', what: 'de la fuerza laboral busca y no encuentra', group: 'Participación', say: v => `Cerca de ${Math.round(v)} de cada 100 personas que trabajan o buscan trabajo no encuentran empleo.`, def: 'Desocupados entre la población económicamente activa de 14 años a más.' },
  { id: 'adecuado', name: 'Empleo adecuado', what: 'de quienes trabajan, sin subempleo', group: 'Calidad del empleo', say: v => `${Math.round(v)} de cada 100 ocupados no están subempleados por horas ni por ingresos.`, def: 'Ocupados sin subempleo por horas ni por ingresos entre el total de ocupados. Es una aproximación del Observatorio.' },
  { id: 'lfpr', name: 'Actividad', what: 'de mayores de 14 trabaja o busca trabajo', group: 'Participación', say: v => `${Math.round(v)} de cada 100 personas de 14 años a más trabajan o buscan trabajo.`, def: 'Población económicamente activa entre la población en edad de trabajar, de 14 años a más.' },
  { id: 'median_inc_real', name: 'Ingreso mediano', what: `al mes, en soles de ${YEAR}`, group: 'Ingresos y horas', say: (_, f) => `La mitad de quienes reciben ingreso laboral gana menos de ${f(_)} al mes.`, def: `Mediana del ingreso laboral mensual de los ocupados con ingreso, en soles de ${YEAR} de Lima.` },
  { id: 'gap_lfpr', name: 'Brecha de actividad', what: 'entre hombres y mujeres', group: 'Participación', say: v => `La actividad de los hombres supera a la de las mujeres en ${v.toFixed(1)} puntos.`, def: 'Tasa de actividad de hombres menos tasa de actividad de mujeres, en puntos porcentuales.' },
  { id: 'epr', name: 'Ocupación sobre población', group: 'Participación', def: 'Ocupados entre la población de 14 años a más.' },
  { id: 'ur_youth', name: 'Desempleo juvenil', group: 'Jóvenes', def: 'Desocupados entre la población económicamente activa de 15 a 29 años.' },
  { id: 'neet', name: 'Jóvenes que ni estudian ni trabajan', group: 'Jóvenes', def: 'Personas de 15 a 29 años que no estudian ni trabajan entre el total de ese grupo de edad.' },
  { id: 'subemp_hours', name: 'Subempleo por horas', group: 'Calidad del empleo', def: 'Ocupados subempleados por horas entre el total de ocupados.' },
  { id: 'contract_any', name: 'Asalariados con contrato', group: 'Calidad del empleo', def: 'Asalariados con contrato entre el total de asalariados.' },
  { id: 'pension', name: 'Afiliación a pensiones', group: 'Protección', def: 'Ocupados afiliados a un sistema de pensiones entre el total de ocupados.' },
  { id: 'seguro', name: 'Seguro de salud', group: 'Protección', def: 'Ocupados con seguro de salud entre el total de ocupados.' },
  { id: 'mean_inc_real', name: 'Ingreso promedio', group: 'Ingresos y horas', def: `Promedio del ingreso laboral mensual de los ocupados con ingreso, en soles de ${YEAR} de Lima.` },
  { id: 'hours_mean', name: 'Horas por semana', group: 'Ingresos y horas', def: 'Promedio de horas semanales trabajadas por los ocupados.' },
  { id: 'hours_le48', name: 'Ocupados con 48 horas o menos', group: 'Ingresos y horas', def: 'Ocupados que trabajan 48 horas semanales o menos entre el total de ocupados.' },
  { id: 'self_emp', name: 'Trabajo independiente', group: 'Tipo de trabajo', def: 'Trabajadores independientes entre el total de ocupados.' },
  { id: 'tfnr', name: 'Trabajo familiar no remunerado', group: 'Tipo de trabajo', def: 'Trabajadores familiares no remunerados entre el total de ocupados.' },
];
export const SIX = INDICATORS.filter(i => i.what);
export const UNITS: Record<string, string> = { median_inc_real: 'S/', mean_inc_real: 'S/', gap_lfpr: 'pp', hours_mean: 'h' };
export const unitOf = (id: string) => UNITS[id] ?? '%';
export const fmtU = (v: number, u: string) => u === '%' ? v.toFixed(1) + '%' : u === 'S/' ? 'S/' + Math.round(v).toLocaleString('en-US') : `${v.toFixed(1)} ${u}`;
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
