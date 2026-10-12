"""Corre el motor de indicadores para todos los años → out/estimates.parquet"""
import sys, time
import pandas as pd
from olp.config import YEARS, OUT_DIR
from olp.build_person import load_person
from olp.derive import derive
from olp.engine import run_year
years = [int(a) for a in sys.argv[1:]] or YEARS
parts = []
for y in years:
    t = time.time()
    est = run_year(derive(load_person(y)), y)
    parts.append(est)
    print(f"{y}: {len(est):,} estimaciones ({time.time()-t:.0f}s) grades={est.grade.value_counts().to_dict()}", flush=True)
all_ = pd.concat(parts, ignore_index=True)
all_.to_parquet(OUT_DIR / "estimates.parquet", index=False)
print("saved", OUT_DIR / "estimates.parquet", all_.shape)
