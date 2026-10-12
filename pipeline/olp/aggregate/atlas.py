import numpy as np
from .common import *

DIMS = ATLAS["primary"] + ATLAS["secondary"]


def region_rows(est, year=HEADLINE_YEAR):
    rows = []
    for _, cw in CROSSWALK.iterrows():
        rid = cw.ubigeo2
        dom = "lima" if rid in ("15M", "15R") else "dept"
        vals = {d["id"]: cell(pick(est, d["id"], dom, rid, year), nd_for(d["id"])) for d in DIMS}
        rows.append({"id": rid, "name": cw["name"], "region_nat": cw.region_nat, "parent": cw.parent or None, "values": vals})
    # percentile ranks among the 25 departments (LM/LR excluded from ranking), suppressed excluded
    base = [r for r in rows if not r["parent"]]
    for d in DIMS:
        vs = [(r["id"], r["values"][d["id"]]["v"]) for r in base if r["values"][d["id"]]["v"] is not None]
        vals = np.array([v for _, v in vs], dtype=float)
        if not d["higher_better"]:
            vals = -vals
        order = vals.argsort().argsort()
        pct = {rid: int(round(100 * rank / max(len(vals) - 1, 1))) for (rid, _), rank in zip(vs, order)}
        rank = {rid: int(len(vals) - r) for (rid, _), r in zip(vs, order)}
        for r in rows:
            r.setdefault("pct", {})[d["id"]] = pct.get(r["id"])
            r.setdefault("rank", {})[d["id"]] = rank.get(r["id"])
    return rows


def build(est):
    obj = {"year": HEADLINE_YEAR, "n_regions": 25,
           "dims": [{**d, "primary": d in ATLAS["primary"]} for d in DIMS],
           "regions": region_rows(est)}
    return dump(obj, "atlas_regions.json")
