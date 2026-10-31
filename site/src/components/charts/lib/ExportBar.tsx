import { useState } from 'preact/hooks';
import { toSVG, toPNG, toCSV } from './export';
import { fmtNum } from './format';
const show = (v: any) => v == null || v === '' ? '—' : typeof v === 'number' ? fmtNum(v, Number.isInteger(v) ? 0 : 2) : String(v);
// `table`: alternativa en texto del gráfico (los mismos datos del CSV). Se desactiva donde el gráfico ya trae su propia tabla.
export default function ExportBar({ svgRef, rows, name, table = true }: { svgRef: { current: SVGSVGElement | null }; rows?: () => Record<string, any>[]; name: string; table?: boolean }) {
  const [open, setOpen] = useState(false);
  const data = open && rows ? rows() : [];
  return (
    <>
      {rows && table && <details class="data-table" onToggle={e => setOpen((e.currentTarget as HTMLDetailsElement).open)}><summary>Ver los datos en tabla</summary>
        {open && data.length > 0 && <div class="scroll-x" style="max-height:50vh;overflow:auto"><table class="data"><thead><tr>{Object.keys(data[0]).map(c => <th scope="col">{c}</th>)}</tr></thead>
          <tbody>{data.map(r => <tr>{Object.keys(data[0]).map(c => <td>{show(r[c])}</td>)}</tr>)}</tbody></table></div>}</details>}
      <div class="toolbar" style="justify-content:flex-end;gap:6px;margin-top:8px">
        {rows && <button class="btn small" onClick={() => toCSV(rows(), name + '.csv')}>CSV</button>}
        <button class="btn small" onClick={() => svgRef.current && toSVG(svgRef.current, name + '.svg')}>SVG</button>
        <button class="btn small" onClick={() => svgRef.current && toPNG(svgRef.current, name + '.png')}>PNG</button>
      </div>
    </>
  );
}
