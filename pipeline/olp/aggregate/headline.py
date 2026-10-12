from datetime import date
from .common import *
from .narrative import kpi_deltas


def build(est):
    y = HEADLINE_YEAR
    n = int(est[(est.year == y) & (est.indicator == "lfpr") & (est.domain == "national")].iloc[0]["n"])
    pet = float(est[(est.year == y) & (est.indicator == "lfpr") & (est.domain == "national")].iloc[0]["N"])
    kpis = {k: cell(pick(est, k, "national"), nd_for(k)) for k in
            ["lfpr", "epr", "ur", "informality", "gap_lfpr", "median_inc_real", "adecuado", "neet", "ur_youth", "subemp_hours"]}
    by_sex = {k: {s: cell(pick(est, k, "sex", s), nd_for(k)) for s in ("1", "2")} for k in ["lfpr", "epr", "ur", "informality", "median_inc_real", "neet"]}
    by_area = {k: {a: cell(pick(est, k, "area", a), nd_for(k)) for a in ("1", "2")} for k in ["lfpr", "ur", "informality", "median_inc_real"]}
    trend = {k: series(est, k, "national", "all") for k in ["lfpr", "ur", "informality", "median_inc_real", "adecuado", "neet", "gap_lfpr", "subemp_hours"]}
    deltas = {k: kpi_deltas(est, k) for k in kpis}
    by_educ_sex = {k: {f"{s}|{e}": cell(pick(est, k, "sex_educ4", f"{s}|{e}"), nd_for(k)) for s in ("1", "2") for e in ("1", "2", "3", "4")} for k in ["ur", "lfpr", "informality", "median_inc_real"]}
    by_region = {k: {r: cell(pick(est, k, "region_nat", r), nd_for(k)) for r in ("1", "2", "3", "4")} for k in ["lfpr", "ur", "informality", "median_inc_real", "adecuado"]}
    status = dist_cells(est, "status_dist", "national", "all")
    prot = {k: cell(pick(est, k, "national"), nd_for(k)) for k in ["pension", "seguro", "contract_any", "hours_ge60", "subemp_income", "self_emp", "tfnr"]}
    obj = {"year": y, "generated": date.today().isoformat(),
           "source": f"INEI – ENAHO {y}, módulo 500 (fac500a). Elaboración: Observatorio Laboral del Perú.",
           "n_persons": n, "pet_weighted": round(pet), "years": YEARS,
           "kpis": kpis, "deltas": deltas, "by_sex": by_sex, "by_area": by_area, "by_educ_sex": by_educ_sex, "by_region": by_region, "status_dist": status, "protection": prot, "trend": trend}
    return dump(obj, "headline.json")
