const FALLBACK: Record<string, string> = {  // = tokens.css (tema claro), para el render en servidor
  '--seq-1': '#d4e4f3', '--seq-2': '#a8cae8', '--seq-3': '#74a8d8', '--seq-4': '#4286c2', '--seq-5': '#1f5f9e', '--seq-6': '#0d3766',
  '--cat-1': '#c2521f', '--cat-2': '#2266b3', '--cat-3': '#8d3f9e', '--cat-4': '#c49000', '--cat-5': '#12a085', '--cat-6': '#6b7280', '--cat-7': '#d98c5f', '--cat-8': '#3a9fc4', '--cat-9': '#a0601a',
};
const isBrowser = typeof window !== 'undefined' && typeof getComputedStyle === 'function';
export const cssVar = (name: string) => isBrowser ? (getComputedStyle(document.documentElement).getPropertyValue(name).trim() || FALLBACK[name] || '') : (FALLBACK[name] || '');
export const seq = () => [1, 2, 3, 4, 5, 6].map(i => cssVar(`--seq-${i}`));
export const cat = () => [1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => cssVar(`--cat-${i}`));
export const onThemeChange = (cb: () => void) => {
  if (!isBrowser) return () => {};
  const mo = new MutationObserver(cb); mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  const mq = matchMedia('(prefers-color-scheme: dark)'); mq.addEventListener('change', cb);
  return () => { mo.disconnect(); mq.removeEventListener('change', cb); };
};
