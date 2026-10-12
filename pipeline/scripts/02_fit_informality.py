"""Concordancia de la regla de informalidad con ocupinf (INEI) por año; guarda out/informality_agreement.csv."""
import pandas as pd
from olp.config import YEARS, OUT_DIR
from olp.build_person import load_person
from olp.informality import fit, DEFAULT
rows = []
for y in YEARS:
    d = load_person(y)
    if d["ocupinf_inei"].notna().sum() == 0:
        print(y, "sin ocupinf (no validable)"); continue
    f = fit(d); f["year"] = y
    rows.append(f)
    best = f[(f.sector == DEFAULT[0]) & (f.wage == DEFAULT[1])].iloc[0]
    print(f"{y}: regla por defecto concordancia ponderada {best.agree_w*100:.2f}% | tasa regla {best.rate_rule*100:.1f} vs INEI {best.rate_inei*100:.1f}", flush=True)
out = pd.concat(rows)
out.to_csv(OUT_DIR / "informality_agreement.csv", index=False)
