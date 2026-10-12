import pandas as pd
from olp.aggregate.common import load_estimates
from olp import validate
from olp.config import OUT_DIR
pd.set_option("display.width", 220)
df = validate.run(load_estimates())
print(df.to_string())
md = ["# Validación frente a cifras oficiales INEI", "", df.to_markdown(index=False)]
(OUT_DIR / "validation_report.md").write_text("\n".join(md), encoding="utf-8")
print("\nOK:", int(df.ok.sum()), "/", len(df))
