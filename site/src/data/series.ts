// Annual series of one indicator by group and by department, read at build time
// from the per-indicator CSV of the data release (public/data/latest/por_indicador).
import fs from 'node:fs';
import path from 'node:path';

export interface SCell { v: number | null; g: string; n: number; se?: number; lo?: number; hi?: number }
export interface SeriesFile {
  id: string; name: string; unit: string; years: number[]; national: SCell[];
  domains: Record<string, { label: string; groups: { key: string; label: string; cells: SCell[] }[] }>;
  dept: Record<string, { name: string; cells: SCell[] }>;
}

export const SERIES_DOMAINS = ['sex', 'area', 'region_nat', 'age4', 'educ4', 'lengua3', 'etnia6'];
const DATA = path.resolve(process.cwd(), 'public/data');

// Minimal CSV reader: quoted fields may hold commas and doubled quotes.
function parseCsv(text: string): string[][] {
  const rows: string[][] = []; let row: string[] = [], cur = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) { if (ch === '"') { if (text[i + 1] === '"') { cur += '"'; i++; } else quoted = false; } else cur += ch; }
    else if (ch === '"') quoted = true;
    else if (ch === ',') { row.push(cur); cur = ''; }
    else if (ch === '\n') { row.push(cur); rows.push(row); row = []; cur = ''; }
    else if (ch !== '\r') cur += ch;
  }
  if (cur || row.length) { row.push(cur); rows.push(row); }
  return rows;
}

const num = (s: string) => s === '' ? undefined : Number(s);
const EMPTY: SCell = { v: null, g: 'S', n: 0 };

export function hasSeries(file: string) { return fs.existsSync(path.join(DATA, 'latest', file)); }

/** Build the series of an indicator. `file` is the ficha's `file` field (por_indicador/<id>.csv). */
export function loadSeries(id: string, file: string, years: number[], name = '', national: SCell[] = []): SeriesFile {
  const [head, ...rows] = parseCsv(fs.readFileSync(path.join(DATA, 'latest', file), 'utf8'));
  const col = Object.fromEntries(head.map((h, i) => [h, i]));
  const out: SeriesFile = { id, name, unit: '', years, national, domains: {}, dept: {} };
  const slot = () => years.map(() => ({ ...EMPTY }));
  for (const r of rows) {
    const domain = r[col.domain]; if (domain !== 'dept' && !SERIES_DOMAINS.includes(domain)) continue;
    if (r[col.category]) continue; // distributions are not served here
    const yi = years.indexOf(Number(r[col.year])); if (yi < 0) continue;
    out.unit ||= r[col.unit];
    const g = r[col.grade], v = num(r[col.estimate]);
    const cell: SCell = g === 'S' || v == null ? { v: null, g: 'S', n: num(r[col.n]) ?? 0 } : { v: +v.toFixed(2), g, n: num(r[col.n]) ?? 0, se: num(r[col.se]), lo: num(r[col.ci_lo]) == null ? undefined : +num(r[col.ci_lo])!.toFixed(2), hi: num(r[col.ci_hi]) == null ? undefined : +num(r[col.ci_hi])!.toFixed(2) };
    if (domain === 'dept') { (out.dept[r[col.key]] ??= { name: r[col.key_label], cells: slot() }).cells[yi] = cell; continue; }
    const d = (out.domains[domain] ??= { label: r[col.domain_label], groups: [] });
    let grp = d.groups.find(x => x.key === r[col.key]);
    if (!grp) { grp = { key: r[col.key], label: r[col.key_label], cells: slot() }; d.groups.push(grp); }
    grp.cells[yi] = cell;
  }
  for (const d of Object.values(out.domains)) d.groups.sort((a, b) => a.key.localeCompare(b.key, 'en', { numeric: true }));
  return out;
}
