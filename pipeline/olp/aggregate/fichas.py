"""Indicator pages: one JSON per indicator with its documentation, year-by-year comparability and estimates.

Writes `fichas/index.json` (documentation only, for lists and search) and `fichas/<id>.json`.
Documentation comes from config/indicator_docs.yml, indicators.yml, variables.yml and series_breaks.yml.
Suppressed cells go through `cell`, so they never carry a value.
"""
from .common import *

DOCS = load_yaml("indicator_docs.yml")
DERIVED = DOCS["derived"]
YEAR_NOTES = {int(y): t for y, t in (DOCS.get("year_notes") or {}).items()}
VARS = load_yaml("variables.yml")
MODULE_NAME = {"m02": "200 (miembros del hogar)", "m03": "300 (educación)", "m04": "400 (salud)",
               "m05": "500 (empleo e ingresos)", "m34": "Sumaria"}
DOMAINS = ["sex", "area", "region_nat", "age4", "educ4", "lengua3", "etnia6"]
GROUP_VAR = {"sex": "sex"}
GROUP_WORD = {"sex": {1: "hombres", 2: "mujeres"}}
STAT = {"mean": "Promedio", "median": "Mediana", "gini": "Índice de Gini"}


def source_vars():
    """Canonical name -> ENAHO name, module and note."""
    out = {}
    for mod, spec in VARS["modules"].items():
        for name, v in spec["vars"].items():
            out.setdefault(name, {"enaho": v["src"], "module": mod, "module_name": MODULE_NAME[mod], "note": v.get("note", "")})
    return out


SRC = source_vars()


def expand(names):
    """Derived variables in dependency order (inputs first), each listed once."""
    seen = []

    def visit(n):
        if n in seen or n not in DERIVED:
            return
        for u in DERIVED[n].get("uses", []):
            visit(u)
        seen.append(n)
    for n in names:
        visit(n)
    return seen


def own_vars(ind_id):
    """Derived variables an indicator rests on directly."""
    s = IND[ind_id]
    if s["type"] in ("diff", "ratio_median"):
        return own_vars(s["base"]) + [GROUP_VAR[s["group"]]]
    return [v for v in (s.get("num"), s.get("var"), s.get("den"), s.get("filter")) if v]


def enaho_vars(derived):
    names = []
    for d in derived:
        names += DERIVED[d].get("vars", []) if d in DERIVED else [d]
    out, seen = [], set()
    for n in names:
        if n in seen:
            continue
        seen.add(n)
        if n not in SRC:
            raise KeyError(f"variable {n} is not in variables.yml")
        out.append({"name": n, **SRC[n]})
    return out


def label(v):
    return DERIVED[v]["label"]


def measure(ind_id):
    """Numerator and denominator in words, as (role, text) rows."""
    s = IND[ind_id]
    t = s["type"]
    den = label(s["den"]) + (f", {label(s['filter'])}" if s.get("filter") else "") if "den" in s else ""
    if t == "prop":
        return [["Numerador", label(s["num"])], ["Denominador", den]]
    if t in STAT:
        return [["Medida", f"{STAT[t]} de {label(s['var'])}"], ["Población", den]]
    if t == "quantile":
        return [["Medida", f"Percentil {round(s['q'] * 100)} de {label(s['var'])}"], ["Población", den]]
    if t == "dist":
        cats = ", ".join(s.get("labels_es", {}).values())
        return [["Categorías", f"{label(s['var'])}: {cats}"], ["Denominador", den]]
    words = GROUP_WORD[s["group"]]
    base = DOCS["indicators"][s["base"]]["name"].lower()
    op = "menos" if t == "diff" else "entre"
    return [["Cálculo", f"{base} de {words[s['a']]} {op} {base} de {words[s['b']]}"]] + measure(s["base"])[1:]


def breaks_for(ind_id):
    return [b for b in BREAKS if ind_id in b["indicators"]]


def comparability(est, ind_id):
    """One row per year: status (ok, note, break, nd), source of the series and notes."""
    brks = breaks_for(ind_id)
    rows = []
    for y in YEARS:
        r = pick(est, ind_id, "national", "all", y, category=1 if IND[ind_id]["type"] == "dist" else None)
        notes, status, source = [], "ok", None
        for b in brks:
            source = b.get("after_es") if y >= b["year"] else b.get("before_es")
            if y == b["year"]:
                status = "break"
                notes.append(b["label_es"])
        if y in YEAR_NOTES:
            notes.append(YEAR_NOTES[y])
            if status == "ok":
                status = "note"
        if r is None or r["grade"] == "S" or r["est"] != r["est"]:
            status, notes = "nd", ["Sin estimación para este año."]
        rows.append({"year": y, "status": status, "source": source, "notes": notes})
    return rows


def doc(ind_id):
    s, d = IND[ind_id], DOCS["indicators"][ind_id]
    own = own_vars(ind_id)
    derived = expand(own) + [v for v in own if v not in DERIVED]
    return {"id": ind_id, "name": d["name"], "group": d["group"], "def": d["def"].replace("__YEAR__", str(HEADLINE_YEAR)),
            "label": s["label_es"].replace("__YEAR__", str(HEADLINE_YEAR)),
            "unit": s.get("unit") or "", "type": s["type"], "measure": measure(ind_id),
            "rules": [{"name": v, "label": label(v), "rule": DERIVED[v]["rule"]} for v in derived if v in DERIVED],
            "vars": enaho_vars(derived), "breaks": [b["id"] for b in breaks_for(ind_id)],
            "file": f"por_indicador/{ind_id}.csv"}


def dist_series(est, ind_id, domain="national", key="all"):
    labs = IND[ind_id].get("labels_es", {})
    return [{"k": int(k), "label": l, "cells": [cell(pick(est, ind_id, domain, key, y, category=int(k)), nd_for(ind_id)) for y in YEARS]}
            for k, l in labs.items()]


def ficha(est, ind_id):
    nd = nd_for(ind_id)
    out = doc(ind_id) | {"years": YEARS, "year": HEADLINE_YEAR, "comparability": comparability(est, ind_id)}
    if IND[ind_id]["type"] == "dist":
        out["national"] = dist_series(est, ind_id)
        return out
    out["national"] = [cell(pick(est, ind_id, "national", "all", y), nd) for y in YEARS]
    cur = est[(est.indicator == ind_id) & (est.year == HEADLINE_YEAR) & est.category.isna()]
    out["domains"] = {}
    for dom in DOMAINS:
        rows = cur[cur.domain == dom].sort_values("key")
        if len(rows):
            out["domains"][dom] = {"label": DOM[dom]["label_es"],
                                   "groups": [{"key": k, "label": label_for(dom, k), **cell(r, nd)} for k, r in zip(rows.key, rows.to_dict("records"))]}
    dept = cur[cur.domain == "dept"].set_index("key")
    out["dept"] = {k: cell(dept.loc[k].to_dict() | {"indicator": ind_id}, nd) for k in dept.index} if len(dept) else None
    return out


def build(est):
    docs = []
    for ind_id in IND:
        if ind_id not in DOCS["indicators"]:
            raise KeyError(f"{ind_id} has no entry in indicator_docs.yml")
        f = ficha(est, ind_id)
        dump(f, f"fichas/{ind_id}.json")
        docs.append({k: f[k] for k in ("id", "name", "group", "def", "unit", "type", "label")}
                    | {"latest": f["national"][-1] if f["type"] != "dist" else None})
    dump({"year": HEADLINE_YEAR, "groups": list(dict.fromkeys(d["group"] for d in docs)), "indicators": docs}, "fichas/index.json")
    return len(docs)
