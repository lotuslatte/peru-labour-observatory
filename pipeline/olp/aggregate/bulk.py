"""Bulk data product: every estimate in long form, with suppressed cells blank.

Reads the internal estimates and writes public files, so all suppression happens in `public_frame`.
"""
import gzip
import hashlib
import json
import pandas as pd
from .common import *
from ..config import RELEASE

LATEST = SITE_DATA_DIR / "latest"
TEXT = ["indicator", "indicator_label", "unit", "domain", "domain_label", "key", "key_label", "category_label", "grade", "method_note"]
NUMERIC = ["estimate", "se", "rse_pct", "ci_lo", "ci_hi", "population"]
COLS = ["period", "year", "indicator", "indicator_label", "unit", "domain", "domain_label", "key", "key_label",
        "category", "category_label", "estimate", "se", "rse_pct", "ci_lo", "ci_hi", "n", "population", "grade",
        "inconclusive", "method_note"]
COLUMN_DOC = {
    "period": "Reference period: one year, or the pooled years for provinces",
    "year": "Survey year; for pooled provinces, the last year",
    "indicator": "Indicator id", "indicator_label": "Indicator name", "unit": "Unit: %, pp, S/ or h",
    "domain": "Breakdown id", "domain_label": "Breakdown name", "key": "Group code within the breakdown",
    "key_label": "Group name", "category": "Category code in distribution indicators",
    "category_label": "Category name", "estimate": "Weighted estimate", "se": "Design-based standard error",
    "rse_pct": "Relative standard error, %", "ci_lo": "Lower limit of the 95% interval",
    "ci_hi": "Upper limit of the 95% interval", "n": "Unweighted sample count",
    "population": "Expanded population of the group", "grade": "A reliable, B caution, S suppressed",
    "inconclusive": "1 when a gap's 95% interval includes no gap", "method_note": "Method caveat for this value",
}


def domain_labels():
    return {d: spec["label_es"] for d, spec in DOM.items()} | {"prov": "Provincia"}


def method_note(ind, year, domain):
    if domain == "prov" and any(ind in b["indicators"] for b in BREAKS):
        return "pooled_across_method_break"
    return next((b["id"] for b in BREAKS if ind in b["indicators"] and year >= b["year"]), "")


def public_frame() -> pd.DataFrame:
    est = load_estimates().assign(period=lambda d: d.year.astype(str))
    prov = pd.read_parquet(OUT_DIR / "estimates_prov.parquet").drop(columns="n_psu")
    pool = load_yaml("province_indicators.yml")["pool_years"]
    prov["period"] = f"{min(pool)}-{max(pool)}"
    prov["category"] = prov.category.astype(float)
    df = pd.concat([est, prov], ignore_index=True)
    names = pd.read_csv(CONFIG_DIR / "prov_names.csv", dtype=str).set_index("ubigeo4").name.to_dict()
    pairs = df[["domain", "key"]].drop_duplicates()
    labels = {(d, k): names[k] if d == "prov" else label_for(d, k) for d, k in zip(pairs.domain, pairs.key)}
    df["key_label"] = [labels[p] for p in zip(df.domain, df.key)]
    df["domain_label"] = df.domain.map(domain_labels())
    df["indicator_label"] = df.indicator.map(lambda i: IND[i]["label_es"])
    df["unit"] = df.indicator.map(lambda i: IND[i].get("unit") or "")
    cats = {i: {int(k): v for k, v in IND[i].get("labels_es", {}).items()} for i in df.indicator.unique()}
    df["category_label"] = [cats[i].get(int(c), str(int(c))) if c == c else "" for i, c in zip(df.indicator, df.category)]
    df["method_note"] = [method_note(i, y, d) for i, y, d in zip(df.indicator, df.year, df.domain)]
    df["rse_pct"] = df.rse * 100
    df = df.rename(columns={"est": "estimate", "lo": "ci_lo", "hi": "ci_hi", "N": "population"})
    suppressed = df.grade == "S"
    df.loc[suppressed, NUMERIC] = None
    df["inconclusive"] = [0 if s else int(inconclusive(i, a, b)) for i, a, b, s in zip(df.indicator, df.ci_lo, df.ci_hi, suppressed)]
    df[NUMERIC] = df[NUMERIC].round(3)
    df["population"] = df.population.round(0)
    return df[COLS].sort_values(["indicator", "domain", "key", "category", "year"], na_position="first").reset_index(drop=True)


def write_gzip_csv(df, path):
    with gzip.GzipFile(path, "wb", mtime=0, compresslevel=9) as f:  # mtime=0 keeps the bytes reproducible
        f.write(df.to_csv(index=False).encode("utf-8"))


def write_stata(df, path):
    d = df.copy()
    for c in TEXT + ["period"]:
        d[c] = pd.Categorical(d[c].fillna(""))
    d = d.rename(columns={"indicator_label": "ind_label", "category_label": "cat_label", "domain_label": "dom_label", "key_label": "grp_label"})
    source = {"ind_label": "indicator_label", "cat_label": "category_label", "dom_label": "domain_label", "grp_label": "key_label"}
    labels = {c: COLUMN_DOC[source.get(c, c)][:80] for c in d.columns}
    d.to_stata(path, write_index=False, version=118, variable_labels=labels, data_label="Observatorio Laboral del Peru")


def codebook(df):
    rows = []
    for i, spec in IND.items():
        rows.append({"kind": "indicator", "id": i, "label": spec["label_es"], "unit": spec.get("unit") or "", "note": spec.get("note_es", "")})
    for d, l in domain_labels().items():
        if d in set(df.domain):
            rows.append({"kind": "domain", "id": d, "label": l, "unit": "", "note": ""})
    for c, doc in COLUMN_DOC.items():
        rows.append({"kind": "column", "id": c, "label": doc, "unit": "", "note": ""})
    for b in BREAKS:
        rows.append({"kind": "method_note", "id": b["id"], "label": b["label_en"], "unit": "", "note": b["label_es"]})
    rows.append({"kind": "method_note", "id": "pooled_across_method_break", "label": "The pooled years mix both sides of a method break", "unit": "", "note": ""})
    return pd.DataFrame(rows)


def write_excel(df, code, path):
    keep = df[df.domain.isin(["national", "sex", "area", "region_nat", "age4", "educ4", "lengua3", "etnia6", "dept", "lima", "prov"])]
    with pd.ExcelWriter(path, engine="openpyxl") as x:
        keep.to_excel(x, sheet_name="estimates", index=False)
        code.to_excel(x, sheet_name="dictionary", index=False)
    return len(keep)


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build():
    (LATEST / "por_indicador").mkdir(parents=True, exist_ok=True)
    (LATEST / "por_dominio").mkdir(exist_ok=True)
    df = public_frame()
    write_gzip_csv(df, LATEST / "estimates.csv.gz")
    df.to_parquet(LATEST / "estimates.parquet", index=False)
    for i, g in df.groupby("indicator"):
        g.to_csv(LATEST / "por_indicador" / f"{i}.csv", index=False)
    for d, g in df.groupby("domain"):
        write_gzip_csv(g, LATEST / "por_dominio" / f"{d}.csv.gz")
    write_stata(df, LATEST / "observatorio_laboral.dta")
    code = codebook(df)
    code.to_csv(LATEST / "codebook.csv", index=False)
    xlsx_rows = write_excel(df, code, LATEST / "observatorio_laboral.xlsx")
    meta = {"data_version": RELEASE["data_version"], "headline_year": HEADLINE_YEAR, "years": [YEARS[0], YEARS[-1]],
            "license": "CC-BY-4.0", "source": "INEI, ENAHO", "rows": len(df), "suppressed_rows": int((df.grade == "S").sum()),
            "xlsx_rows": xlsx_rows, "columns": COLUMN_DOC,
            "indicators": {i: {"label": s["label_es"], "unit": s.get("unit")} for i, s in IND.items()}}
    (LATEST / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    files = [{"path": str(p.relative_to(LATEST)), "bytes": p.stat().st_size, "sha256": sha256(p)}
             for p in sorted(LATEST.rglob("*")) if p.is_file() and p.name != "manifest.json"]
    (LATEST / "manifest.json").write_text(json.dumps({"data_version": RELEASE["data_version"], "files": files}, indent=1))
    return len(df), sum(f["bytes"] for f in files)
