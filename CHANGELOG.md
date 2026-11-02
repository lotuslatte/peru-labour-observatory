# Changelog

Data and method changes, newest first. Data versions use the `YYYY.N` form.

## Unreleased

### Added
- ENAHO 2025 (INEI survey 1031): headline year, 12 months, 25 departments.
- `config/release.yml` as the single source for years, survey codes and minimum wage. `config/official/<year>.yml` holds targets by year, and validation fails if the latest year has none.
- Nine indicators, two domains and eight compendium tables already defined in the configuration are now published.
- `config/series_breaks.yml` declares method breaks. Comparisons across a break are flagged as not comparable and never reported as significant.
- `LICENSE`, `CITATION.cff` and this changelog.

### Changed
- Site redesign: the home page shows six headline figures, each indicator has its own page with trend, map, groups and data tabs, and `/explorar/` builds a query with its own CSV. The menu now has four items; Atlas, Compendio, Análisis and Novedades moved to the footer.

### Fixed
- Indicator maps: department borders now match. They were thinned ring by ring and left gaps; `departamentos.topo.json` is rebuilt from the shapefile with shared borders, and the map adds a Lima and Callao inset.
- `/datos/` explains the cell format in a table and no longer scrolls sideways on phones.
- Embed snippets pointed to a URL without the site base and returned 404.
- Atlas embed snippets now offer every dimension.

### Method
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
