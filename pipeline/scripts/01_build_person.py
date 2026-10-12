"""Construye person_{year}.parquet para los años indicados (por defecto todos)."""
import sys, time
from olp.config import YEARS
from olp.build_person import build
years = [int(a) for a in sys.argv[1:]] or YEARS
for y in years:
    t = time.time()
    df = build(y)
    print(f"{y}: {len(df):,} personas PET, PET ponderada {df.w500.sum()/1e6:.2f} M ({time.time()-t:.0f}s)", flush=True)
