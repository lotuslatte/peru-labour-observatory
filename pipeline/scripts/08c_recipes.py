"""Write site/public/data/recipes/<id>.json with the Stata, R and Python recipe of each indicator.

Only recipes that reproduced the published figure in the last run of 09_check_recipes.py are written;
an indicator with no verified language gets no file and its page shows no recipe block.
"""
import json
import sys
import pandas as pd
from olp.config import HEADLINE_YEAR, OUT_DIR, SITE_DATA_DIR as SITE_DATA
from olp.engine import IND
from olp.aggregate import fichas
from olp import recipes

check = pd.read_csv(OUT_DIR / "recipes_check.csv")
ok = {(r.indicator, r.lang) for r in check.itertuples() if r.ok}
out = SITE_DATA / "recipes"
out.mkdir(exist_ok=True)
for old in out.glob("*.json"):
    old.unlink()
n = 0
for ind in IND:
    name = fichas.DOCS["indicators"][ind]["name"]
    own = fichas.own_vars(ind)
    code = recipes.build(ind, name, fichas.expand(own) + [v for v in own if v not in fichas.DERIVED])
    code = {lang: text for lang, text in code.items() if (ind, lang) in ok}
    if not code:
        continue
    (out / f"{ind}.json").write_text(json.dumps({"id": ind, "year": HEADLINE_YEAR, "code": code}, ensure_ascii=False), encoding="utf-8")
    n += 1
print(f"{n} of {len(IND)} indicators with a verified recipe")
sys.exit(0)
