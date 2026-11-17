// /data/series/<id>.json: annual series of an indicator by group and department.
// Fetched on demand by the indicator page (map by year, comparison) and by the explorer.
import type { APIRoute } from 'astro';
import fs from 'node:fs';
import path from 'node:path';
import { loadSeries, hasSeries } from '../../../data/series';
import { slim } from '../../../data/ui';

const DATA = path.resolve(process.cwd(), 'public/data');
const ficha = (id: string) => JSON.parse(fs.readFileSync(path.join(DATA, `fichas/${id}.json`), 'utf8'));

export function getStaticPaths() {
  const idx = JSON.parse(fs.readFileSync(path.join(DATA, 'fichas/index.json'), 'utf8'));
  return idx.indicators.filter((d: any) => d.type !== 'dist' && hasSeries(ficha(d.id).file)).map((d: any) => ({ params: { id: d.id } }));
}

export const GET: APIRoute = ({ params }) => {
  const f = ficha(params.id!);
  return new Response(JSON.stringify(loadSeries(f.id, f.file, f.years, f.name, f.national.map(slim))), { headers: { 'Content-Type': 'application/json' } });
};
