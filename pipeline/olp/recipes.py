"""Self-contained Stata, R and Python recipes that reproduce one national indicator for the headline year.

Each recipe loads module 500 (plus 300, 400 or the sumaria when its variables need them), builds the
derived variables from config/recipes.yml in dependency order, declares the design (PSU conglome,
strata department x estrato, singleton strata centred) and estimates. Every recipe ends by defining
`est` (a scalar, or a vector for distributions) so scripts/09_check_recipes.py can compare it with
the published value.
"""
import re
from .config import HEADLINE_YEAR, RMV, load_yaml
from .engine import IND

CODE = load_yaml("recipes.yml")["derived"]
Y = HEADLINE_YEAR
KEYS = ["conglome", "vivienda", "hogar", "codperso"]
# Variables that live outside module 500, by file. A module is merged only when its variables appear.
EXTRA = {
    "300": (f"enaho01a-{Y}-300.dta", KEYS, ["p307"]),
    "400": (f"enaho01a-{Y}-400.dta", KEYS, ["p401g1", "p401g2"] + [f"p419{k}" for k in range(1, 9)]),
    "sumaria": (f"sumaria-{Y}.dta", KEYS[:3], ["pobreza"]),
}
SCALE = {"%": 100}
FMT = {"%": ("{:.1f}", "%"), "pp": ("{:.1f}", " pp"), "S/": ("{:,.0f}", ""), "S/h": ("{:.2f}", ""), "h": ("{:.1f}", ""), "ratio": ("{:.3f}", "")}
STATA_FMT = {"%": "%6.1f", "pp": "%6.1f", "S/": "%9.0fc", "S/h": "%6.2f", "h": "%6.1f", "ratio": "%6.3f"}


def fill(s: str) -> str:
    return s.replace("__YEAR__", str(Y)).replace("__RMV__", str(RMV[Y]))


def lines(derived, lang):
    out = []
    for v in derived:
        if v in CODE:
            out += [fill(x) for x in CODE[v][lang]]
    return out


def modules(text):
    return [k for k, (_, _, cols) in EXTRA.items() if any(re.search(rf"\b{c}\b", text) for c in cols)]


def needed(text, cols):
    return [c for c in cols if re.search(rf"\b{c}\b", text)]


def spec_parts(ind):
    """(type, value variable, denominator, filter, base spec) with gaps resolved to their base."""
    s = IND[ind]
    if s["type"] in ("diff", "ratio_median"):
        b = IND[s["base"]]
        return s["type"], b.get("num") or b.get("var"), b["den"], b.get("filter"), s
    return s["type"], s.get("num") or s.get("var"), s["den"], s.get("filter"), s


def unit_of(ind):
    s = IND[ind]
    if s["type"] == "diff":
        return "pp"
    return s.get("unit") or ""


# ---------------------------------------------------------------- Stata
def stata(ind, name, derived):
    t, y, den, filt, s = spec_parts(ind)
    body = lines(derived, "stata")
    cond = f"{den} == 1" + (f" & {filt} == 1" if filt else "")
    u = unit_of(ind)
    k = 100 if u in ("%", "pp") else 1
    f = STATA_FMT.get(u, "%9.3f")
    est = []
    if t in ("prop", "mean"):
        est = [f"svy, subpop(if {cond}): mean {y}",
               f"scalar est = {k} * _b[{y}]",
               f"display \"{name}, {Y}: \" {f} est \"   error estándar: \" %6.2f {k} * _se[{y}]"]
    elif t in ("median", "quantile"):
        q = round(s.get("q", 0.5) * 100)
        est = ["* Weighted percentile. The Observatory adds a Woodruff interval, which Stata 14 does not compute.",
               f"_pctile {y} [pw = fac500a] if {cond}, p({q})",
               "scalar est = r(r1)", f"display \"{name}, {Y}: \" {f} est"]
    elif t == "gini":
        est = ["* Weighted Gini. The Observatory's standard error comes from a bootstrap of PSUs.",
               "preserve", f"keep if {cond} & !missing({y})", f"sort {y}",
               f"gen double wy = fac500a * {y}", "gen double acum = sum(wy)",
               "gen double t = fac500a * (acum - wy / 2)",
               "quietly summarize fac500a", "scalar W = r(sum)", "quietly summarize wy", "scalar Yt = r(sum)",
               "quietly summarize t", "scalar est = 1 - 2 * r(sum) / (W * Yt)", "restore",
               f"display \"{name}, {Y}: \" %6.3f est"]
    elif t == "dist":
        est = [f"svy, subpop(if {cond} & !missing({y})): proportion {y}",
               "matrix est = 100 * e(b)", "matrix list est, format(%6.1f)"]
    elif t == "diff":
        a, b = s["a"], s["b"]
        est = ["label values p207 .",
               f"svy, subpop(if {cond}): mean {y}, over(p207)",
               f"lincom [{y}]{a} - [{y}]{b}",
               f"scalar est = 100 * r(estimate)",
               f"display \"{name}, {Y}: \" %6.1f est \" puntos   error estándar: \" %6.2f 100 * r(se)"]
    elif t == "ratio_median":
        a, b = s["a"], s["b"]
        est = ["* Ratio of weighted medians. The Observatory's standard error comes from a bootstrap of PSUs.",
               f"_pctile {y} [pw = fac500a] if {cond} & p207 == {a}, p(50)", "scalar qa = r(r1)",
               f"_pctile {y} [pw = fac500a] if {cond} & p207 == {b}, p(50)", "scalar qb = r(r1)",
               "scalar est = qa / qb", f"display \"{name}, {Y}: \" %6.3f est"]
    text = "\n".join(body + est)
    head = [f"* {name}, ENAHO {Y}. Observatorio Laboral del Perú.",
            f"* Put the ENAHO {Y} .dta files in one folder and set it here.",
            "cd \".\"", f"use enaho01a-{Y}-500.dta, clear", "rename *, lower",
            "keep if (p204 == 1 | missing(p204)) & p208a >= 14 & fac500a > 0 & !missing(fac500a)"]
    for m in modules(text):
        f_, keys, cols = EXTRA[m]
        kind = "1:1" if keys == KEYS else "m:1"
        head.append(f"merge {kind} {' '.join(keys)} using {f_}, keepusing({' '.join(needed(text, cols))}) keep(master match) nogenerate")
    design = ["", "gen dept = substr(ubigeo, 1, 2)", "egen estrato_dept = group(dept estrato)",
              "svyset conglome [pw = fac500a], strata(estrato_dept) singleunit(centered)", ""]
    return "\n".join(head + [""] + body + design + est) + "\n"


# ---------------------------------------------------------------- R
R_GINI = """gini <- function(y, w) {
  o <- order(y); y <- y[o]; w <- w[o]; wy <- w * y
  1 - 2 * sum(w * (cumsum(wy) - wy / 2)) / (sum(w) * sum(wy))
}"""
R_WQ = """wq <- function(y, w, q) {  # first value whose weighted cumulative share reaches q
  o <- order(y); y <- y[o]; w <- w[o]; y[which(cumsum(w) / sum(w) >= q)[1]]
}"""


def r(ind, name, derived):
    t, y, den, filt, s = spec_parts(ind)
    body = lines(derived, "r")
    cond = f"{den} %in% 1" + (f" & {filt} %in% 1" if filt else "")
    u = unit_of(ind)
    k = 100 if u in ("%", "pp") else 1
    helpers = []
    if t in ("prop", "mean"):
        est = [f"r <- svymean(~{y}, subset(des, {cond}), na.rm = TRUE)",
               f"est <- {k} * unname(coef(r))", f"cat(\"{name}, {Y}:\", round(est, 2), \"  error estándar:\", round({k} * unname(SE(r)), 3), \"\\n\")"]
    elif t in ("median", "quantile"):
        q = s.get("q", 0.5)
        est = ["# Weighted quantile with a Woodruff interval, as the Observatory computes it",
               f"r <- svyquantile(~{y}, subset(des, {cond}), {q}, na.rm = TRUE, ci = TRUE)",
               "est <- unname(coef(r))", "print(r)"]
    elif t == "gini":
        helpers = [R_GINI]
        est = ["# The Observatory's standard error comes from a bootstrap of PSUs",
               f"s <- subset(d, {cond} & !is.na({y}))", f"est <- gini(s${y}, s$fac500a)",
               f"cat(\"{name}, {Y}:\", round(est, 3), \"\\n\")"]
    elif t == "dist":
        est = [f"r <- svymean(~factor({y}), subset(des, {cond} & !is.na({y})), na.rm = TRUE)",
               "est <- 100 * unname(coef(r))", "print(round(100 * coef(r), 1))"]
    elif t == "diff":
        a, b = s["a"], s["b"]
        w = {1: 0, 2: 0}
        w[a], w[b] = 1, -1
        est = [f"r <- svyby(~{y}, ~p207, subset(des, {cond}), svymean, na.rm = TRUE)",
               f"g <- svycontrast(r, c({w[1]}, {w[2]}))  # group {a} minus group {b}",
               "est <- 100 * unname(coef(g))", f"cat(\"{name}, {Y}:\", round(est, 2), \"puntos  error estándar:\", round(100 * unname(SE(g)), 3), \"\\n\")"]
    elif t == "ratio_median":
        a, b = s["a"], s["b"]
        helpers = [R_WQ]
        est = ["# Ratio of weighted medians; the Observatory's standard error comes from a bootstrap of PSUs",
               f"s <- subset(d, {cond} & !is.na({y}))",
               f"est <- with(subset(s, p207 == {a}), wq({y}, fac500a, 0.5)) / with(subset(s, p207 == {b}), wq({y}, fac500a, 0.5))",
               f"cat(\"{name}, {Y}:\", round(est, 3), \"\\n\")"]
    text = "\n".join(body + est)
    head = [f"# {name}, ENAHO {Y}. Observatorio Laboral del Perú.",
            "library(haven); library(dplyr); library(survey)",
            f"ruta <- \".\"  # folder with the ENAHO {Y} .dta files",
            "leer <- function(f) read_dta(file.path(ruta, f)) |> zap_labels() |> rename_with(tolower)",
            "among <- function(x, m) ifelse(m %in% 1, as.integer(coalesce(as.logical(x), FALSE)), NA_integer_)",
            *helpers, "",
            f"d <- leer(\"enaho01a-{Y}-500.dta\") |> filter(p204 %in% 1 | is.na(p204), p208a >= 14, fac500a > 0)"]
    for m in modules(text):
        f_, keys, cols = EXTRA[m]
        head.append(f"d <- left_join(d, leer(\"{f_}\") |> select({', '.join(keys + needed(text, cols))}), by = c({', '.join(repr(k).replace(chr(39), chr(34)) for k in keys)}))")
    mut = ["d <- d |> mutate(", ",\n".join("  " + x if not x.startswith("#") else "  " + x for x in body).replace("#", "#"), ")"]
    # comments inside mutate() cannot carry a trailing comma
    mlines = []
    for x in body:
        mlines.append(("  " + x) if x.startswith("#") else ("  " + x + ","))
    if mlines:
        last = max(i for i, x in enumerate(mlines) if not x.lstrip().startswith("#"))
        mlines[last] = mlines[last].rstrip(",")
    mut = ["d <- d |> mutate("] + mlines + [")"]
    design = ["", "options(survey.lonely.psu = \"adjust\")  # singleton strata centred on the grand mean",
              "d <- d |> mutate(estrato_dept = paste(substr(ubigeo, 1, 2), estrato))",
              "des <- svydesign(ids = ~conglome, strata = ~estrato_dept, weights = ~fac500a, data = d, nest = TRUE)", ""]
    return "\n".join(head + [""] + mut + design + est) + "\n"


# ---------------------------------------------------------------- Python
PY_HELPERS = '''def among(x, m):
    """x as 0/1 where m equals 1, missing elsewhere."""
    return x.astype(float).where(m.eq(1))


def se_total(z):
    """Taylor standard error of a total of scores z: PSUs within strata, singleton strata centred."""
    p = pd.DataFrame({"h": d.estrato_dept, "c": d.conglome, "z": z}).groupby(["h", "c"]).z.sum().reset_index()
    n = p.groupby("h").z.transform("size")
    dev = p.z - p.groupby("h").z.transform("mean")
    v = (n / (n - 1) * dev ** 2)[n > 1].sum() + ((p.z[n == 1] - p.z.mean()) ** 2).sum()
    return v ** 0.5


def ratio(y, m):
    """Weighted mean of y where m is true, with its design standard error."""
    m = m & y.notna()
    w = d.fac500a.where(m, 0)
    r = (w * y.fillna(0)).sum() / w.sum()
    return r, se_total(w * (y.fillna(0) - r) / w.sum())
'''
PY_DIFF = '''

def diff(y, ma, mb):
    """Difference of two weighted means with their design covariance."""
    (ra, _), (rb, _) = ratio(y, ma), ratio(y, mb)
    z = 0
    for r, m, sign in ((ra, ma, 1), (rb, mb, -1)):
        m = m & y.notna()
        w = d.fac500a.where(m, 0)
        z = z + sign * w * (y.fillna(0) - r) / w.sum()
    return ra - rb, se_total(z)
'''
PY_WQ = '''

def wquantile(y, m, q):
    """First value whose weighted cumulative share reaches q."""
    s = pd.DataFrame({"y": y, "w": d.fac500a})[m & y.notna()].sort_values("y", kind="stable")
    return s.y.iloc[(s.w.cumsum() / s.w.sum()).searchsorted(q)]
'''
PY_GINI = '''

def gini(y, m):
    s = pd.DataFrame({"y": y, "w": d.fac500a})[m & y.notna()].sort_values("y", kind="stable")
    wy = s.w * s.y
    return 1 - 2 * (s.w * (wy.cumsum() - wy / 2)).sum() / (s.w.sum() * wy.sum())
'''


def python(ind, name, derived):
    t, y, den, filt, s = spec_parts(ind)
    body = lines(derived, "py")
    cond = f'd.{den}.eq(1)' + (f' & d.{filt}.eq(1)' if filt else "")
    u = unit_of(ind)
    k = 100 if u in ("%", "pp") else 1
    fmt, suf = FMT.get(u, ("{:.3f}", ""))
    helpers = PY_HELPERS
    if t in ("prop", "mean"):
        est = [f"est, se = ratio(d.{y}, {cond})", f"est, se = {k} * est, {k} * se" if k != 1 else "",
               f'print(f"{name}, {Y}: {{est:{fmt[2:-1]}}}{suf}   error estándar: {{se:.2f}}")']
    elif t in ("median", "quantile"):
        helpers += PY_WQ
        est = ["# The Observatory adds a Woodruff interval to this quantile",
               f"est = wquantile(d.{y}, {cond}, {s.get('q', 0.5)})", f'print(f"{name}, {Y}: {{est:{fmt[2:-1]}}}")']
    elif t == "gini":
        helpers += PY_GINI
        est = ["# The Observatory's standard error comes from a bootstrap of PSUs",
               f"est = gini(d.{y}, {cond})", f'print(f"{name}, {Y}: {{est:.3f}}")']
    elif t == "dist":
        labels = IND[ind]["labels_es"]
        est = [f"categorias = {dict((int(a), b) for a, b in labels.items())}",
               "est = {}", "for k, nombre in categorias.items():",
               f"    e, se = ratio(d.{y}.eq(k).astype(float).where(d.{y}.notna()), {cond})",
               "    est[k] = 100 * e", '    print(f"{nombre}: {100 * e:.1f}%   error estándar: {100 * se:.2f}")']
    elif t == "diff":
        helpers += PY_DIFF
        a, b = s["a"], s["b"]
        est = [f"est, se = diff(d.{y}, {cond} & d.p207.eq({a}), {cond} & d.p207.eq({b}))",
               "est, se = 100 * est, 100 * se", f'print(f"{name}, {Y}: {{est:.1f}} puntos   error estándar: {{se:.2f}}")']
    elif t == "ratio_median":
        helpers += PY_WQ
        a, b = s["a"], s["b"]
        est = ["# Ratio of weighted medians; the Observatory's standard error comes from a bootstrap of PSUs",
               f"est = wquantile(d.{y}, {cond} & d.p207.eq({a}), 0.5) / wquantile(d.{y}, {cond} & d.p207.eq({b}), 0.5)",
               f'print(f"{name}, {Y}: {{est:.3f}}")']
    est = [x for x in est if x]
    text = "\n".join(body + est)
    head = [f"# {name}, ENAHO {Y}. Observatorio Laboral del Perú.", "import numpy as np", "import pandas as pd", "",
            f'RUTA = "."  # folder with the ENAHO {Y} .dta files', f"CLAVES = {KEYS}", "",
            "", "def leer(archivo, columnas=None):",
            '    t = pd.read_stata(f"{RUTA}/{archivo}", convert_categoricals=False, columns=columnas)',
            "    t.columns = t.columns.str.lower()", "    return t", "", "",
            helpers.rstrip(), "", "",
            f'd = leer("enaho01a-{Y}-500.dta")',
            "d = d[d.p204.fillna(1).eq(1) & (d.p208a >= 14) & (d.fac500a > 0)].reset_index(drop=True)"]
    for m in modules(text):
        f_, keys, cols = EXTRA[m]
        kk = "CLAVES" if keys == KEYS else "CLAVES[:3]"
        head.append(f'd = d.merge(leer("{f_}", {kk} + {needed(text, cols)}), on={kk}, how="left")')
    design = ['d["estrato_dept"] = d.ubigeo.str[:2] + "-" + d.estrato.astype(int).astype(str)', ""]
    return "\n".join(head + design + body + [""] + est) + "\n"


def build(ind, name, derived):
    return {"stata": stata(ind, name, derived), "r": r(ind, name, derived), "python": python(ind, name, derived)}
