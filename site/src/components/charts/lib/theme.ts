const FALLBACK: Record<string, string> = {  // = tokens.css (tema claro), para el render en servidor
  '--seq-1': '#e6f1ee', '--seq-2': '#bfdcd5', '--seq-3': '#8fc2b7', '--seq-4': '#5aa093', '--seq-5': '#2c7d70', '--seq-6': '#0f5148',
  '--cat-1': '#a8244f', '--cat-2': '#167a6e', '--cat-3': '#b7791f', '--cat-4': '#2f5d9e', '--cat-5': '#7b4fa6', '--cat-6': '#6f7288', '--cat-7': '#d98c5f', '--cat-8': '#3aa3a0', '--cat-9': '#8a6d4b',
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
