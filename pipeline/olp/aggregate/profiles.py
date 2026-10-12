from .common import *
from .atlas import region_rows, DIMS
from .narrative import profile_summary

DUMB = [("sex", ["1", "2"], "dept_sex"), ("age4", ["1", "2", "3", "4"], "dept_age4"), ("lengua3", ["1", "2"], "dept_lengua3"), ("area", ["1", "2"], "dept_area")]
DUMB_IND = ["lfpr", "ur", "informality", "median_inc_real", "adecuado", "neet"]


def build(est):
    rows = region_rows(est)
    paths = []
    for r in rows:
        rid = r["id"]
        dom = "lima" if r["parent"] else "dept"
        nrow = pick(est, "lfpr", dom, rid)
        prof = {"id": rid, "name": r["name"], "region_nat": r["region_nat"], "parent": r["parent"], "year": HEADLINE_YEAR,
                "n": int(nrow["n"]) if nrow is not None else 0, "pet_weighted": round(float(nrow["N"])) if nrow is not None else None,
                "dims": r["values"], "pct": r.get("pct", {}), "rank": r.get("rank", {}),
                "status_dist": dist_cells(est, "status_dist", dom, rid),
                "sector_dist": dist_cells(est, "sector_dist", dom, rid),
                "educ_dist": dist_cells(est, "educ_dist", dom, rid),
                "inc_pct": {q: cell(pick(est, q, dom, rid), 0) for q in ["inc_p10", "inc_p25", "median_inc_real", "inc_p75", "inc_p90", "mean_inc_real"]},
                "quality": {k: cell(pick(est, k, dom, rid), nd_for(k)) for k in ["subemp_hours", "subemp_income", "hours_mean", "hours_ge60", "contract_any", "pension", "seguro", "firm_small", "self_emp", "tfnr", "ur_youth"]},
                "dumbbells": {}, "trend": {}}
        if dom == "dept":
            for g, keys, dd in DUMB:
                labs = DOM[g].get("labels_es") or recode_labels(DOM[g]["recode"])
                prof["dumbbells"][g] = {k: {key: {"label": labs.get(int(key), key), **cell(pick(est, k, dd, f"{rid}|{key}"), nd_for(k))} for key in keys} for k in DUMB_IND}
        prof["trend"] = {k: series(est, k, dom, rid) for k in ["lfpr", "ur", "informality", "median_inc_real", "adecuado"]}
        prof["summary"] = profile_summary(est, rid, dom, r["name"], r.get("rank", {}), r.get("pct", {}), [d for d in DIMS if d in ATLAS["primary"]])
        paths.append(dump(prof, f"profiles/{rid}.json"))
    return paths
