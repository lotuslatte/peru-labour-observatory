from datetime import date
import pandas as pd
from .common import *
from ..config import load_yaml, RSE_A, RSE_B, MIN_N
from ..informality import DEFAULT


def build(est):
    ipc = pd.read_csv(CONFIG_DIR / "ipc_lima_2014_2024.csv", comment="#")
    agree = OUT_DIR / "informality_agreement.csv"
    ag = {}
    if agree.exists():
        a = pd.read_csv(agree); a = a[(a.sector == DEFAULT[0]) & (a.wage == DEFAULT[1])]
        ag = {int(r.year): {"agree_w": round(float(r.agree_w), 4), "rate_rule": round(float(r.rate_rule) * 100, 2), "rate_inei": round(float(r.rate_inei) * 100, 2)} for r in a.itertuples()}
    obj = {"generated": date.today().isoformat(), "years": YEARS, "headline_year": HEADLINE_YEAR,
           "grades": {"A": f"RSE < {int(RSE_A*100)} %", "B": f"RSE {int(RSE_A*100)}–{int(RSE_B*100)} %", "S": f"RSE ≥ {int(RSE_B*100)} % o n < {MIN_N}"},
           "indicators": {k: {kk: v.get(kk) for kk in ("label_es", "label_en", "unit", "type")} for k, v in IND.items()},
           "domains": {k: {"label_es": v["label_es"], "labels": {str(kk): vv for kk, vv in (v.get("labels_es") or (recode_labels(v["recode"]) if "recode" in v else {})).items()}} for k, v in DOM.items()},
           "ipc": ipc.to_dict(orient="records"),
           "informality_rule": {"sector": "sin RUC (p510a1 == 3)", "wage": "sin seguro de salud ligado al trabajo (EsSalud/EPS/privado/FFAA) y sin afiliación a pensión, o contrato por locación de servicios (5) o sin contrato (7)", "tfnr": "siempre informal", "source_by_year": {str(y): ("inei_ocupinf" if y in ag else "rule") for y in YEARS}, "agreement": ag},
           "design": {"weight": "fac500a", "psu": "conglome", "strata": "departamento × estrato (pseudo-estratos)", "variance": "Linealización de Taylor; estratos con un PSU centrados en la media global", "median": "IC de Woodruff"},
           "sample": {int(y): int(est[(est.year == y) & (est.indicator == "lfpr") & (est.domain == "national")].iloc[0]["n"]) for y in YEARS}}
    return dump(obj, "meta.json")
