# Changelog

Data and method changes, newest first. Data versions use the `YYYY.N` form.

## Unreleased

### Added
- Nine indicators, two domains and eight compendium tables already defined in the configuration are now published.
- `config/series_breaks.yml` declares method breaks. Comparisons across a break are flagged as not comparable and never reported as significant.
- `LICENSE`, `CITATION.cff` and this changelog.

### Fixed
- Embed snippets pointed to a URL without the site base and returned 404.
- Atlas embed snippets now offer every dimension.

### Method
- Informal employment: INEI stopped publishing `ocupinf` from 2024. Values from 2024 use the Observatory rule, so 2023 to 2024 and 2014 to 2024 changes are not comparable.

## 2026-10-31

### Changed
- Data regenerated on 2026-10-12: decomposition components are graded by n, not RSE.
- EPEN validation targets are labelled as reference values, not annual ENAHO.

### Added
- Validation gate with documented known failures, synthetic tests, 404 and robots pages.
