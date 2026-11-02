# Changelog

Data and method changes, newest first. Data versions use the `YYYY.N` form.

## Unreleased

### Data release
- Version 2026.1 is the first numbered release: `/data/latest/` holds every estimate in CSV, Parquet, Stata and Excel, one file per indicator and per breakdown, a codebook and a manifest with SHA-256 hashes. Fixed copies are attached to the GitHub Release.

### Added
- `/atlas/provincias/` rebuilt with tabs for map, relation, gaps and typologies, a province search and a zoom by department. Maps gain a comparison with Peru in which a territory differs only if its 95% interval excludes the national value.
- `territorios.json`: gaps within departments, four province groups by k-means and spatial autocorrelation, built only from public cells plus 2017 census population.
- ENAHO 2025 (INEI survey 1031): headline year, 12 months, 25 departments.
- `config/release.yml` as the single source for years, survey codes and minimum wage. `config/official/<year>.yml` holds targets by year, and validation fails if the latest year has none.
- Nine indicators, two domains and eight compendium tables already defined in the configuration are now published.
- `config/series_breaks.yml` declares method breaks. Comparisons across a break are flagged as not comparable and never reported as significant.
- `LICENSE`, `CITATION.cff` and this changelog.

### Changed
- Atlas, Compendio, Análisis, Datos, Novedades and department pages now share the open editorial layout. Compendio is a searchable list whose tables open on demand; detail on the other pages moved into expandable sections. URLs and downloads stay the same.
- New palette for the whole site: warm paper, night-blue text, terracotta accent and a blue map scale, checked for color-blind separation. On maps, darker now always means a higher value, and classes are quantiles with their cuts in the legend.
- Site redesign: the home page shows six headline figures, each indicator has its own page with trend, map, groups and data tabs, and `/explorar/` builds a query with its own CSV. The menu now has four items; Atlas, Compendio, Análisis and Novedades moved to the footer.

### Fixed
- Department summaries now write figures as S/1,177 and 82.2%, and no longer call an eight-sentence list «cinco frases».
- The province map drew all 196 provinces in one color with an empty legend. It now colors them and rebuilds `provincias.topo.json` with shared borders.
- Sideways scroll on `/acerca/metodologia/`, `/analisis/` and `/atlas/provincias/`; site and chart text is now at least 12 px.
- Indicator maps: department borders now match. They were thinned ring by ring and left gaps; `departamentos.topo.json` is rebuilt from the shapefile with shared borders, and the map adds a Lima and Callao inset.
- `/datos/` explains the cell format in a table and no longer scrolls sideways on phones.
- Embed snippets pointed to a URL without the site base and returned 404.
- Atlas embed snippets now offer every dimension.

### Method
- Industry corrected. CIIU codes arrive as numbers without their leading zero, so class 0111 was read as division 11 and agriculture and mining were counted as manufacturing. In 2025 agriculture and fishing is now 23.3% of employment, mining 1.3% and manufacturing 9.4%, against 32.7% for manufacturing before. Everything by industry changes, and so do models that control for it: the adjusted informality gap by sex moves from 4.7 to 5.0 pp, the adjusted income gap from -31.7% to -30.8%, and the indigenous-language informality gap from 3.5 to 3.1 pp. Headline indicators do not change.
- Province groups are a descriptive partition: silhouette 0.25, resampling stability 0.74 (adjusted Rand index), and 0.74 when informality is left out. Moran's I runs 0.22 to 0.36, and few local clusters survive the 5% false discovery correction.
- A cell with a standard error of exactly 0 can no longer get grade A, since identical sampled units do not prove precision. Only Moho (Puno), informality 100.0, changes from A to B. `atlas_provincias.json` adds the national value of the same 2023 to 2025 pool.
- Real income is now in soles of the latest year (2025), rebased every release. Earlier real values rise by the 2024 to 2025 Lima CPI change (1.5%); nominal income and rates do not change.
- Lima CPI now comes from the deflators INEI publishes with ENAHO (i00, dpto 15). The series matches BCRP PN38705PM for 2014 to 2024.
- The informality shift-share now covers 2014 to 2023, the last years both measured with `ocupinf`, instead of crossing the 2024 break.
- Provincial estimates pool 2023 to 2025. Informality in that pool mixes `ocupinf` (2023) and the Observatory rule.
- ENAHO informality runs 2.2 to 2.7 pp above EPEN in 2024 and 2025. The Observatory rule does not explain this: in 2014 to 2023 it runs 0.2 to 1.9 pp below `ocupinf`, 0.2 pp in 2023.
- The story moved to `/historias/panorama/`; the old URL redirects.
- Informal employment: INEI stopped publishing `ocupinf` from 2024. Values from 2024 use the Observatory rule, so 2023 to 2024 and 2014 to 2024 changes are not comparable.

## 2026-10-31

### Changed
- Data regenerated on 2026-10-12: decomposition components are graded by n, not RSE.
- EPEN validation targets are labelled as reference values, not annual ENAHO.

### Added
- Validation gate with documented known failures, synthetic tests, 404 and robots pages.
