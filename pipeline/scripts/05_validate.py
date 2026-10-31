"""Valida contra cifras oficiales; sale con error si hay fallos fuera de config/validation_known.yml."""
import sys
import pandas as pd
from olp.aggregate.common import load_estimates
from olp import validate
from olp.config import OUT_DIR
pd.set_option("display.width", 220)
df = validate.run(load_estimates())
print(df.to_string())
md = ["# Validación frente a cifras oficiales INEI", "", df.to_markdown(index=False)]
(OUT_DIR / "validation_report.md").write_text("\n".join(md), encoding="utf-8")
bad = validate.unexpected(df)
print("\nOK:", int(df.ok.sum()), "/", len(df), "| known failures:", int((~df.ok).sum()) - len(bad), "| unexpected:", len(bad))
if len(bad):
    print("\nERROR — unexpected validation failures:\n", bad.to_string())
    sys.exit(1)
