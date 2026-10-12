from .common import *
from .smooth import add_smooth

TREND_IND = ["lfpr", "epr", "ur", "ur_youth", "informality", "adecuado", "subemp_hours", "neet", "median_inc_real",
             "mean_inc_real", "hours_mean", "hours_le48", "contract_any", "pension", "seguro", "gap_lfpr", "self_emp", "tfnr"]


def build(est):
    s = {"national": {k: series(est, k, "national", "all") for k in TREND_IND}}
    for dom, keys in [("sex", ["1", "2"]), ("area", ["1", "2"]), ("region_nat", ["1", "2", "3", "4"]),
                      ("lengua3", ["1", "2"]), ("age4", ["1", "2", "3", "4"]), ("educ4", ["1", "2", "3", "4"]), ("etnia6", ["1", "2", "3", "4", "5"]), ("sex_educ4", [f"{s}|{e}" for s in "12" for e in "1234"]), ("sex_age4", [f"{s}|{a}" for s in "12" for a in "1234"])]:
        s[dom] = {k: {key: series(est, k, dom, key) for key in keys} for k in TREND_IND}
    s["dept"] = {rid: {k: series(est, k, "lima" if rid in ("15M", "15R") else "dept", rid) for k in ["lfpr", "ur", "informality", "median_inc_real", "adecuado"]}
                 for rid in CROSSWALK.ubigeo2}
    obj = {"years": YEARS, "series": s, "smooth": add_smooth(s),
           "labels": {dom: {str(k): v for k, v in (DOM[dom].get("labels_es") or recode_labels(DOM[dom]["recode"])).items()} for dom in ["sex", "area", "region_nat", "lengua3", "age4", "educ4", "etnia6"]},
           "notes": {"2020": "ENAHO 2020: levantamiento parcialmente telefónico por la pandemia; comparar con cautela.",
                     "2024": "ENAHO 2024: INEI no publica la variable ocupinf; la informalidad se calcula con la regla del Observatorio (ver Metodología)."}}
    return dump(obj, "trends.json")
