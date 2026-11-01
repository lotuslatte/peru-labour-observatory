"""Compara estimaciones con cifras oficiales INEI (official/<año>.yml y official_series.yml)."""
import pandas as pd
from .config import load_yaml, deflators, CONFIG_DIR, HEADLINE_YEAR, OUT_DIR, SITE_DATA_DIR
from .aggregate.common import pick

_DOMKEY = {"national": ("national", "all"), "area_1": ("area", "1"), "area_2": ("area", "2"), "lima_15M": ("lima", "15M"),
           "sex_area_1|1": ("sex_area", "1|1"), "sex_area_2|1": ("sex_area", "2|1")}


def run(est) -> pd.DataFrame:
    rows = []
    for path in sorted((CONFIG_DIR / "official").glob("*.yml")):
        o = load_yaml(f"official/{path.name}")
        for t in o["targets"]:
            dom = t["domain"]
            key = "all" if dom == "national" else str(t["key"])
            if dom == "area":
                key = {"urbano": "1", "rural": "2"}[t["key"]]
            if dom == "age4":
                key = {"14-24": "1"}[t["key"]]
            r = pick(est, t["indicator"], dom, key, o["year"])
            tol = t.get("tolerance_pp", o["tolerance_pp"])
            rows.append({"year": o["year"], "indicator": t["indicator"], "domain": f"{dom}:{key}", "official": t["value"],
                         "observatorio": None if r is None else round(float(r["est"]), 2), "tolerance": tol, "source": t["source"]})
    ser = load_yaml("official_series.yml")
    for ind, doms in ser.items():
        for dk, yearvals in doms.items():
            dom, key = _DOMKEY[dk]
            for y, v in yearvals.items():
                if ind == "mean_inc_nominal":
                    r = pick(est, "mean_inc_real", dom, key, y)
                    ipc = deflators()
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
    df.to_csv(SITE_DATA_DIR / "validation.csv", index=False)
    return df


def unexpected(df: pd.DataFrame) -> pd.DataFrame:
    """Filas que deben romper el pipeline: estimación ausente, o fallo no listado en validation_known.yml."""
    known = {(k["year"], k["indicator"], k["domain"]) for k in load_yaml("validation_known.yml")["known"]}
    listed = pd.Series([(r.year, r.indicator, r.domain) in known for r in df.itertuples()], index=df.index)
    return df[df.observatorio.isna() | (~df.ok & ~listed)]


def has_headline_targets(df: pd.DataFrame) -> bool:
    """False when the latest year would be published without any official comparison."""
    return bool((df.year == HEADLINE_YEAR).any())
