PY=/home/xerox/.venvs/research/bin/python
export PYTHONPATH=pipeline
.PHONY: pipeline person informality engine aggregate validate geo test site dev
pipeline: person informality engine aggregate geo validate
check:        ; $(PY) pipeline/scripts/00_check_inputs.py
person:       ; $(PY) pipeline/scripts/01_build_person.py $(YEARS)
informality:  ; $(PY) pipeline/scripts/02_fit_informality.py
engine:       ; $(PY) pipeline/scripts/03_run_engine.py
aggregate:    ; $(PY) pipeline/scripts/04_aggregate.py
validate:     ; $(PY) pipeline/scripts/05_validate.py
geo:          ; $(PY) pipeline/scripts/06_geo.py
test:         ; cd pipeline && ../$(PY) -m pytest -q
site:         ; cd site && npm install && npm run build
dev:          ; cd site && npm run dev
