"""Inventario de archivos ENAHO por módulo y año; alerta si un archivo parece parcial (trimestral)."""
import pyreadstat, pandas as pd
from olp.config import YEARS, OUT_DIR
from olp.files import enaho_file
rows = []
for y in YEARS:
    for m in ("m02", "m03", "m04", "m05", "m34"):
        try:
            p = enaho_file(m, y)
            reader = pyreadstat.read_sav if p.suffix.lower() == ".sav" else pyreadstat.read_dta
            _, meta = reader(str(p), metadataonly=True)
            rows.append({"year": y, "module": m, "file": p.name, "rows": meta.number_rows, "cols": len(meta.column_names)})
        except FileNotFoundError as e:
            rows.append({"year": y, "module": m, "file": None, "rows": 0, "cols": 0})
inv = pd.DataFrame(rows)
inv["median_rows_module"] = inv.groupby("module")["rows"].transform("median")
inv["flag"] = (inv["rows"] < 0.6 * inv["median_rows_module"]).map({True: "PARTIAL/MISSING", False: ""})
inv.to_csv(OUT_DIR / "inventory.csv", index=False)
print(inv.to_string())
bad = inv[inv.flag != ""]
if len(bad):
    print("\nWARNING — partial or missing files:\n", bad.to_string())
