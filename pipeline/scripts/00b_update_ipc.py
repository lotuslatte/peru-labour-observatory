"""Writes config/ipc_lima.csv from the INEI annual deflators bundled with ENAHO sumaria.

Usage: 00b_update_ipc.py <path to deflactores_base<year>_new.dta>
Column i00 for dpto 15 is the Lima CPI annual average; it matches BCRP PN38705PM once rebased.
"""
import sys
import pandas as pd
from olp.config import CONFIG_DIR, RELEASE, HEADLINE_YEAR

df = pd.read_stata(sys.argv[1], convert_categoricals=False)
lima = df[df.dpto == 15].set_index("aniorec")["i00"].sort_index()
lima = lima[lima.index >= RELEASE["first_year"]].round(6)
lima.index = lima.index.astype(int)
if HEADLINE_YEAR not in lima.index:
    sys.exit(f"{sys.argv[1]} has no deflator for {HEADLINE_YEAR}")
head = f"# Lima CPI, annual average, base {HEADLINE_YEAR}=1. Source: INEI ENAHO deflators (i00, dpto 15), sumaria ConstVarGasto package.\n"
out = CONFIG_DIR / "ipc_lima.csv"
out.write_text(head + lima.rename("ipc_lima").rename_axis("year").to_csv(), encoding="utf-8")
print("wrote", out, len(lima), "years")
