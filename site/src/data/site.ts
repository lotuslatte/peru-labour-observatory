// Site identity and navigation, shared by the layout, the footer and the search palette.
export const SITE_NAME = 'Observatorio Laboral del Perú';

export const NAV: [string, string][] = [
  ['/indicadores/', 'Indicadores'],
  ['/atlas/', 'Territorios'],
  ['/historias/', 'Historias'],
  ['/datos/', 'Datos'],
  ['/acerca/metodologia/', 'Método'],
];

export const FOOTER: { title: string; links: [string, string][] }[] = [
  { title: 'Indicadores', links: [['/indicadores/', 'Todos los indicadores'], ['/explorar/', 'Armar una consulta'], ['/novedades/', 'Qué cambió'], ['/compendio/', 'Compendio de tablas']] },
  { title: 'Territorios', links: [['/atlas/', 'Departamentos'], ['/atlas/provincias/', 'Provincias']] },
  { title: 'Leer', links: [['/historias/panorama/', 'Panorama laboral'], ['/analisis/', 'Análisis con controles'], ['/glosario/', 'Glosario'], ['/preguntas/', 'Preguntas frecuentes']] },
  { title: 'Datos y método', links: [['/datos/', 'Descargas'], ['/acerca/metodologia/', 'Metodología'], ['/acerca/validacion/', 'Validación'], ['/acerca/escuela-de-encuestas/', 'Escuela de encuestas'], ['/acerca/', 'Acerca de']] },
];
