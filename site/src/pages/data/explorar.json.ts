// Slim annual series for the explorer, built from the public trends file with suppressed cells blanked.
import { loadTrends, loadAtlas } from '../../data/loaders';
import { INDICATORS, unitOf, slim } from '../../data/ui';
export function GET() {
  const tr = loadTrends();
  const ids = INDICATORS.map(i => i.id);
  const series: Record<string, any> = { national: {} , dept: {} };
  for (const i of ids) series.national[i] = tr.series.national[i].map(slim);
  for (const d of ['sex', 'area', 'region_nat', 'age4', 'educ4', 'lengua3', 'etnia6']) {
    series[d] = {};
    for (const i of ids) series[d][i] = Object.fromEntries(Object.entries(tr.series[d][i]).map(([k, cs]: any) => [k, cs.map(slim)]));
  }
  for (const [rid, inds] of Object.entries<any>(tr.series.dept)) for (const [i, cs] of Object.entries<any>(inds)) if (ids.includes(i)) (series.dept[i] ??= {})[rid] = cs.map(slim);
  const body = { years: tr.years, breaks: tr.breaks, labels: tr.labels, regions: loadAtlas().regions.map(r => ({ id: r.id, name: r.name })), ind: Object.fromEntries(INDICATORS.map(i => [i.id, { label: i.name, unit: unitOf(i.id) }])), series };
  return new Response(JSON.stringify(body), { headers: { 'Content-Type': 'application/json' } });
}
