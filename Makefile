PY ?= /home/xerox/.venvs/research/bin/python
export PYTHONPATH=pipeline
.PHONY: pipeline check person informality engine models province aggregate geo territory cards bulk index validate test site dev
pipeline: check person informality engine models province aggregate geo territory cards bulk index validate
check:        ; $(PY) pipeline/scripts/00_check_inputs.py
person:       ; $(PY) pipeline/scripts/01_build_person.py $(YEARS)
informality:  ; $(PY) pipeline/scripts/02_fit_informality.py
engine:       ; $(PY) pipeline/scripts/03_run_engine.py
models:       ; $(PY) pipeline/scripts/03c_models.py
province:     ; $(PY) pipeline/scripts/03b_run_province.py
aggregate:    ; $(PY) pipeline/scripts/04_aggregate.py
geo:          ; $(PY) pipeline/scripts/06_geo.py
territory:    ; $(PY) pipeline/scripts/06b_territory.py
cards:        ; $(PY) pipeline/scripts/07_cards.py
bulk:         ; $(PY) pipeline/scripts/08b_bulk.py
index:        ; $(PY) pipeline/scripts/08_index.py
validate:     ; $(PY) pipeline/scripts/05_validate.py
test:         ; $(PY) -m pytest -q pipeline/tests
site:         ; cd site && npm install && npm run build
dev:          ; cd site && npm run dev
