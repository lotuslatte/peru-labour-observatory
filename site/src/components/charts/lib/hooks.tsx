import { useEffect, useState } from 'preact/hooks';
import { onThemeChange } from './theme';
import { getJson } from './fetch';

/** Contador que cambia cuando cambia el tema; va en las dependencias del efecto que dibuja. */
export function useThemeTick(): number {
  const [tick, setTick] = useState(0);
  useEffect(() => onThemeChange(() => setTick(t => t + 1)), []);
  return tick;
}

/** JSON remoto con estado de carga y de error. `url` nulo = no pedir nada. */
export function useJson<T = any>(url: string | null): { data: T | null; error: boolean } {
  const [data, setData] = useState<T | null>(null); const [error, setError] = useState(false);
  useEffect(() => { if (!url) return; let live = true; getJson<T>(url).then(d => live && setData(d)).catch(e => { console.error(e); if (live) setError(true); }); return () => { live = false; }; }, [url]);
  return { data, error };
}

/** Regiones y dimensiones del atlas: las de las props si vienen; si no, se piden a `src` (una sola descarga, cacheada por el navegador). */
export function useAtlasData<R, D>(regions: R[] | undefined, dims: D[] | undefined, src: string): { regions: R[] | null; dims: D[] | null; error: boolean } {
  const { data, error } = useJson<{ regions: R[]; dims: D[] }>(regions && dims ? null : src);
  return { regions: regions ?? data?.regions ?? null, dims: dims ?? data?.dims ?? null, error };
}

export const NS_TITLE = 'Brecha no concluyente: el intervalo de confianza de 95 % incluye la ausencia de brecha.';
/** Marca para brechas cuyo IC incluye la ausencia de brecha. */
export function NsMark({ compact = false }: { compact?: boolean }) {
  return <span class="nsmark" title={NS_TITLE}>{compact ? <><span aria-hidden="true">n.c.</span><span class="sr-only">brecha no concluyente</span></> : 'no concluyente'}</span>;
}

export function LoadState({ error }: { error: boolean }) {
  return error
    ? <p class="small load-error" role="alert">No se pudieron cargar los datos de este gráfico. Recarga la página o descárgalos desde <a href="/datos/">Datos</a>.</p>
    : <p class="small muted" role="status">Cargando datos…</p>;
}
