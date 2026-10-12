"""Frases automáticas (es) para perfiles y titulares: comparaciones con significancia de diseño."""
import math
from .common import *

Z = 1.959964


def delta(a, b):
    """a - b con SE combinada (muestras independientes) y significancia."""
    if a is None or b is None or a["grade"] == "S" or b["grade"] == "S":
        return None
    d = float(a["est"] - b["est"]); se = math.sqrt(float(a["se"]) ** 2 + float(b["se"]) ** 2) if a["se"] == a["se"] and b["se"] == b["se"] else float("nan")
    return {"d": round(d, 2), "se": round(se, 3) if se == se else None, "sig": bool(se == se and abs(d) > Z * se)}


def fmt(v, unit):
    if v is None: return "—"
    if unit == "S/": return f"S/ {v:,.0f}".replace(",", " ")
    if unit == "pp": return f"{v:+.1f} pp"
    return f"{v:.1f} %"


def profile_summary(est, rid, dom, name, rank, pct, dims) -> list[str]:
    s = []
    lf = pick(est, "lfpr", dom, rid); ur = pick(est, "ur", dom, rid); inf = pick(est, "informality", dom, rid); inc = pick(est, "median_inc_real", dom, rid); ad = pick(est, "adecuado", dom, rid)
    nlf = pick(est, "lfpr", "national"); nur = pick(est, "ur", "national"); ninf = pick(est, "informality", "national"); ninc = pick(est, "median_inc_real", "national"); nad = pick(est, "adecuado", "national")
    def cmp(a, b, unit, better_high, what):
        dl = delta(a, b)
        if dl is None: return None
        if not dl["sig"]: return f"{what} ({fmt(float(a['est']), unit)}) no difiere significativamente del promedio nacional ({fmt(float(b['est']), unit)})."
        dirw = "por encima" if dl["d"] > 0 else "por debajo"
        good = (dl["d"] > 0) == better_high
        tone = "una ventaja" if good else "una desventaja"
        return f"{what} es {fmt(float(a['est']), unit)}, {fmt(abs(dl['d']), 'pp' if unit == '%' else unit).replace('+', '')} {dirw} del promedio nacional ({fmt(float(b['est']), unit)}): {tone} estadísticamente significativa."
    for x in [cmp(inf, ninf, "%", False, "La tasa de empleo informal"), cmp(inc, ninc, "S/", True, "El ingreso laboral mediano"), cmp(ur, nur, "%", False, "La tasa de desempleo"), cmp(lf, nlf, "%", True, "La participación laboral"), cmp(ad, nad, "%", True, "El empleo adecuado")]:
        if x: s.append(x)
    # ranks
    if rank:
        best = sorted([(k, v) for k, v in rank.items() if v and any(d["id"] == k for d in dims)], key=lambda kv: kv[1])[:2]
        worst = sorted([(k, v) for k, v in rank.items() if v and any(d["id"] == k for d in dims)], key=lambda kv: -kv[1])[:2]
        lab = {d["id"]: d["label_es"].split(" (")[0].lower() for d in dims}
        if len(best) >= 2 and len(worst) >= 2: s.append(f"Entre los 25 departamentos, {name} ocupa sus mejores posiciones en {lab[best[0][0]]} (puesto {best[0][1]}) y {lab[best[1][0]]} (puesto {best[1][1]}), y las peores en {lab[worst[0][0]]} (puesto {worst[0][1]}) y {lab[worst[1][0]]} (puesto {worst[1][1]}).")
    # trend 2014→2024
    inf14 = pick(est, "informality", dom, rid, 2014); inc14 = pick(est, "median_inc_real", dom, rid, 2014)
    dl = delta(inf, inf14); di = delta(inc, inc14)
    if dl: s.append(f"Desde 2014 la informalidad {'subió' if dl['d'] > 0 else 'bajó'} {abs(dl['d']):.1f} pp" + (" (cambio significativo)" if dl["sig"] else " (cambio no significativo)") + (f" y el ingreso mediano real {'creció' if di['d'] > 0 else 'cayó'} {abs(di['d']):,.0f} soles de 2024" + (" (significativo)." if di["sig"] else " (no significativo).") if di else "."))
    # gender gap
    g = pick(est, "gap_lfpr", dom, rid)
    if g is not None and g["grade"] != "S":
        s.append(f"La brecha de participación entre hombres y mujeres es de {float(g['est']):.1f} puntos" + (", mayor" if float(g["est"]) > float(pick(est, "gap_lfpr", "national")["est"]) else ", menor") + " que la nacional.")
    return s


def kpi_deltas(est, ind, dom="national", key="all"):
    cur = pick(est, ind, dom, key, HEADLINE_YEAR)
    out = {}
    for lab, y in (("d1", HEADLINE_YEAR - 1), ("d10", 2014)):
        out[lab] = delta(cur, pick(est, ind, dom, key, y))
    return out
