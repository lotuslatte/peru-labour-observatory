"""Territorial analysis from public province cells: gaps, typologies and spatial clusters.

Reads only the public atlas, so suppressed cells stay blank. Results go to territorios.json.
"""
import json
import warnings
import geopandas as gpd
import numpy as np
from esda.moran import Moran, Moran_Local
from libpysal.weights import Queen, w_subset
from scipy.stats import false_discovery_control
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from ..config import PROV_SHP, SITE_DATA_DIR

SEED = 20261101
TYPE_DIMS = ["informality", "lfpr", "seguro", "adecuado", "median_inc_real", "self_emp"]
SPATIAL_DIMS = TYPE_DIMS + ["firm_small", "hours_le48"]
PERMUTATIONS = 9999


def load():
    atlas = json.loads((SITE_DATA_DIR / "atlas_provincias.json").read_text())
    g = gpd.read_file(PROV_SHP)[["IDPROV", "POBTOTAL", "geometry"]]
    g["id"] = g.IDPROV.astype(str).str.zfill(4)
    g["geometry"] = g.geometry.make_valid()
    g = g.dissolve(by="id", aggfunc={"POBTOTAL": "sum"}).reset_index()
    return atlas, g


def value(r, ind):
    return r["values"].get(ind, {}).get("v")


def gaps(atlas):
    """Largest and smallest province per department and indicator, with intervals."""
    out = {}
    for d in atlas["dims"]:
        rows = {}
        for r in atlas["regions"]:
            c = r["values"].get(d["id"], {})
            if c.get("v") is not None:
                rows.setdefault(r["parent"], []).append((c["v"], r["name"], c.get("lo"), c.get("hi")))
        res = []
        for dept, xs in rows.items():
            if len(xs) < 3:
                continue
            xs.sort(key=lambda x: x[0])
            lo, hi = xs[0], xs[-1]
            res.append({"dept": dept, "n": len(xs), "min": {"v": lo[0], "name": lo[1], "lo": lo[2], "hi": lo[3]},
                        "max": {"v": hi[0], "name": hi[1], "lo": hi[2], "hi": hi[3]},
                        "range": round(hi[0] - lo[0], 1), "clear": bool(lo[3] < hi[2])})
        out[d["id"]] = sorted(res, key=lambda x: -x["range"])
    return out


def typologies(atlas, pop):
    regs = [r for r in atlas["regions"] if all(value(r, i) is not None for i in TYPE_DIMS)]
    X = np.array([[value(r, i) for i in TYPE_DIMS] for r in regs], dtype=float)
    Z = (X - X.mean(0)) / X.std(0)
    fit = lambda k, A: KMeans(k, n_init=50, random_state=SEED).fit(A)
    sil = {k: float(silhouette_score(Z, fit(k, Z).labels_)) for k in range(3, 8)}
    k = max(sil, key=sil.get)
    labels = fit(k, Z).labels_
    rng = np.random.default_rng(SEED)
    ari = []
    for _ in range(100):  # stability against resampling provinces
        s = rng.choice(len(Z), len(Z))
        ari.append(adjusted_rand_score(labels, fit(k, Z[s]).predict(Z)))
    drop = TYPE_DIMS.index("informality")  # informality pools two methods, so test without it
    no_inf = adjusted_rand_score(labels, fit(k, np.delete(Z, drop, 1)).labels_)
    w = np.array([pop[r["id"]] for r in regs], dtype=float)
    groups = []
    for g in range(k):
        m = labels == g
        groups.append({"id": g, "n": int(m.sum()), "pop_share": round(float(w[m].sum() / w.sum() * 100), 1),
                       "mean": {i: round(float(np.average(X[m, j], weights=w[m])), 1) for j, i in enumerate(TYPE_DIMS)},
                       "z": {i: round(float(Z[m, j].mean()), 2) for j, i in enumerate(TYPE_DIMS)},
                       "examples": [r["name"] for r, _ in sorted(((r, pop[r["id"]]) for r, l in zip(regs, labels) if l == g), key=lambda x: -x[1])[:5]]})
    name_groups(groups)
    return {"dims": TYPE_DIMS, "k": k, "silhouette": {str(a): round(b, 3) for a, b in sil.items()},
            "stability_ari": round(float(np.median(ari)), 3), "ari_without_informality": round(float(no_inf), 3),
            "groups": groups, "province": {r["id"]: int(l) for r, l in zip(regs, labels)},
            "excluded": len(atlas["regions"]) - len(regs)}


def name_groups(groups):
    """Names follow the profile, so a rerun that reorders the groups keeps them right."""
    by_income = sorted(groups, key=lambda x: x["mean"]["median_inc_real"])
    by_income[0]["name"] = "Bajos ingresos y trabajo independiente"
    by_income[-1]["name"] = "Urbana con más empleo formal"
    middle = sorted(by_income[1:-1], key=lambda x: x["mean"]["seguro"])
    for g, name in zip(middle, ["Ingreso medio con menos seguro", "Ingreso medio con más seguro", "Ingreso medio, otro perfil", "Ingreso medio, cuarto perfil"]):
        g["name"] = name


def spatial(atlas, g):
    w_all = Queen.from_dataframe(g, ids=g.id.tolist(), use_index=False, silence_warnings=True)
    out = {}
    for ind in SPATIAL_DIMS:
        vals = {r["id"]: value(r, ind) for r in atlas["regions"] if value(r, ind) is not None}
        keep = [i for i in g.id if i in vals and w_all.cardinalities.get(i, 0) > 0]
        w = w_subset(w_all, keep, silence_warnings=True)
        w.transform = "r"
        y = np.array([vals[i] for i in w.id_order], dtype=float)
        np.random.seed(SEED)  # esda Moran draws from the global generator
        gm = Moran(y, w, permutations=PERMUTATIONS)
        lm = Moran_Local(y, w, permutations=PERMUTATIONS, seed=SEED)
        q = false_discovery_control(lm.p_sim, method="bh")
        kinds = {1: "HH", 2: "LH", 3: "LL", 4: "HL"}
        out[ind] = {"moran_i": round(float(gm.I), 3), "p": round(float(gm.p_sim), 4), "n": len(y),
                    "cluster": {i: kinds[int(c)] for i, c, p in zip(w.id_order, lm.q, q) if p < 0.05}}
    return out


def build():
    atlas, g = load()
    pop = {i: int(p) for i, p in zip(g.id, g.POBTOTAL)}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        doc = {"years": atlas["years"], "seed": SEED, "pop": pop, "gaps": gaps(atlas),
               "typologies": typologies(atlas, pop), "spatial": spatial(atlas, g)}
    path = SITE_DATA_DIR / "territorios.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    return path
