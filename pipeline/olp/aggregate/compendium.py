import pandas as pd
from .common import *
from ..config import load_yaml

TABLES = load_yaml("compendium_tables.yml")
COLS = ["table_id", "year", "domain", "row_key", "row_label", "indicator", "category", "col_label", "estimate", "se", "rse", "ci_lo", "ci_hi", "n", "grade", "unit"]


def _label(indicator, category):
    spec = IND[indicator]
    if category is not None and category == category:
        return f"{spec['label_es']}: {spec.get('labels_es', {}).get(int(category), int(category))}"
    return spec["label_es"]


def table_frame(est, t) -> pd.DataFrame:
    years = YEARS if t["years"] == "all" else t["years"]
    sub = est[est.indicator.isin(t["indicators"]) & est.domain.isin(t["domains"]) & est.year.isin(years)].copy()
    sub["row_label"] = [label_for(d, k) for d, k in zip(sub.domain, sub.key)]
    sub["col_label"] = [_label(i, c) for i, c in zip(sub.indicator, sub.category)]
    sub["unit"] = sub.indicator.map(lambda i: IND[i].get("unit"))
    sup = sub.grade == "S"
    for c in ["est", "se", "rse", "lo", "hi"]:
        sub.loc[sup, c] = None
    out = sub.rename(columns={"key": "row_key", "est": "estimate", "lo": "ci_lo", "hi": "ci_hi"})
    out["table_id"] = t["id"]
    out["rse"] = out["rse"] * 100
    out = out[COLS].round(3)
    return out.sort_values(["year", "domain", "row_key", "indicator", "category"])


def special_frames(est):
    frames = {}
    # sample sizes
    ss = est[(est.indicator.isin(["lfpr", "informality"])) & est.domain.isin(["national", "dept", "lima"])]
    ss = ss.assign(row_label=[label_for(d, k) for d, k in zip(ss.domain, ss.key)],
                   what=ss.indicator.map({"lfpr": "Personas 14+ (n)", "informality": "Ocupados (n)"}))
    frames["sample_sizes"] = ss.pivot_table(index=["row_label"], columns=["what", "year"], values="n").reset_index()
    p = OUT_DIR / "informality_agreement.csv"
    if p.exists():
        a = pd.read_csv(p)
        frames["informality_agreement"] = a[(a.sector == "A") & (a.wage == "noins_nopens_or_c57")][["year", "agree_w", "agree_unw", "rate_rule", "rate_inei"]].round(4)
    v = OUT_DIR / "validation.csv"
    if v.exists():
        frames["validation"] = pd.read_csv(v)
    return frames


def build(est):
    index = []
    specials = special_frames(est)
    for t in TABLES["tables"]:
        if "special" in t:
            df = specials.get(t["special"], pd.DataFrame())
        else:
            df = table_frame(est, t)
        fn = f"compendium/{t['id']}.csv"
        p = SITE_DATA_DIR / fn
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(p, index=False, encoding="utf-8")
        index.append({"id": t["id"], "section": t["section"], "section_title": TABLES["sections"][t["section"]],
                      "title": t["title"], "file": fn, "rows": int(len(df)),
                      "indicators": t.get("indicators", []), "domains": t.get("domains", []), "years": t.get("years", [])})
    dump({"sections": TABLES["sections"], "tables": index}, "compendium_index.json")
    return index
