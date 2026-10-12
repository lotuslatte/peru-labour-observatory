# Observatorio Laboral del Perú

Sitio: https://lotuslatte.github.io/peru-labour-observatory/

Observatorio abierto del mercado laboral peruano construido a partir de los microdatos de la
Encuesta Nacional de Hogares (ENAHO, INEI), módulo 500 "Empleo e ingresos", 2014–2024.
Réplica peruana de https://indialabourobservatory.com/.

- `pipeline/` — Python: carga, armonización, indicadores con errores estándar de diseño (linealización de Taylor),
  grados de confiabilidad por RSE, y exportación de contratos JSON/CSV para el sitio.
- `site/` — Astro 5 + Preact + D3: sitio estático (atlas departamental, perfiles, historias, compendio, metodología).

## Quickstart
```bash
make pipeline   # requiere el espejo ENAHO en /home/xerox/Documents/03_data/inei/enaho/data
make site       # npm install && npm run build en site/
make validate   # compara titulares 2024 con cifras oficiales INEI
```
Licencia de datos y sitio: CC-BY 4.0. Fuente: INEI – ENAHO.

Prototipo en desarrollo, abierto a colaboración y financiamiento:
[Favio Samillan](https://lotuslatte.github.io).
