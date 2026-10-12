"""Compara estimaciones con cifras oficiales INEI (official_2024.yml y official_series.yml)."""
import pandas as pd
from .config import load_yaml, OUT_DIR, HEADLINE_YEAR
from .aggregate.common import pick

_DOMKEY = {"national": ("national", "all"), "area_1": ("area", "1"), "area_2": ("area", "2"), "lima_15M": ("lima", "15M"),
           "sex_area_1|1": ("sex_area", "1|1"), "sex_area_2|1": ("sex_area", "2|1")}


def run(est) -> pd.DataFrame:
    rows = []
    o24 = load_yaml("official_2024.yml")
    for t in o24["targets"]:
        dom = t["domain"]
        key = "all" if dom == "national" else str(t["key"])
        if dom == "area":
            key = {"urbano": "1", "rural": "2"}[t["key"]]
        if dom == "age4":
            key = {"14-24": "1"}[t["key"]]
        r = pick(est, t["indicator"], dom, key, o24["year"])
        tol = t.get("tolerance_pp", o24["tolerance_pp"])
        rows.append({"year": o24["year"], "indicator": t["indicator"], "domain": f"{dom}:{key}", "official": t["value"],
                     "observatorio": None if r is None else round(float(r["est"]), 2), "tolerance": tol, "source": t["source"]})
    ser = load_yaml("official_series.yml")
    for ind, doms in ser.items():
        for dk, yearvals in doms.items():
            dom, key = _DOMKEY[dk]
            for y, v in yearvals.items():
                if ind == "mean_inc_nominal":
                    r = pick(est, "mean_inc_real", dom, key, y)
                    ipc = pd.read_csv(OUT_DIR.parent / "config" / "ipc_lima_2014_2024.csv", comment="#").set_index("year")["deflator_to_2024"]
                    obs = None if r is None else round(float(r["est"]) / float(ipc.loc[y]), 1)
                    tol = 0.05 * v
                else:
                    r = pick(est, ind, dom, key, y)
                    obs = None if r is None else round(float(r["est"]), 2)
                    tol = 0.5 if ind != "informality" else 1.0
                rows.append({"year": y, "indicator": ind, "domain": dk, "official": v, "observatorio": obs, "tolerance": tol,
                             "source": "INEI, Indicadores de empleo ENAHO (tablas 2007–2021)"})
    df = pd.DataFrame(rows)
    df["diff"] = (df.observatorio - df.official).round(2)
    df["ok"] = df["diff"].abs() <= df.tolerance
    df.to_csv(OUT_DIR / "validation.csv", index=False)
    return df
