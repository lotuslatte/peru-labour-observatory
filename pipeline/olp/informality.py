"""Regla de empleo informal (definición INEI/OIT) reconstruida a partir de p507/p510a1/p510b/seguro/pensión,
validada contra `ocupinf` (2014–2023). Se aplica a 2024, donde INEI no incluye `ocupinf` en el archivo."""
import numpy as np
import pandas as pd

VARIANTS = {
    # sector informal de la unidad productiva
    "sector": {
        "A": lambda d: d["sunat_reg"].eq(3),                                     # sin RUC
        "B": lambda d: d["sunat_reg"].eq(3) | (d["sunat_reg"].eq(2) & d["books"].eq(2)),  # sin RUC o natural sin libros
        "C": lambda d: d["sunat_reg"].ne(1),                                     # no persona jurídica
    },
    # protección de asalariados
    "wage": {
        "pension": lambda d: d["pension_none"].eq(5),
        "essalud": lambda d: d["ins_essalud"].ne(1),
        "essalud_eps_priv": lambda d: ~_ins_work(d),
        # Mejor ajuste (98.4 % de concordancia con ocupinf 2023): sin seguro ligado al trabajo Y sin pensión,
        # o contrato por locación de servicios (5) / sin contrato (7).
        "noins_nopens_or_c57": lambda d: (~_ins_work(d) & d["pension_none"].eq(5)) | d["contract"].isin([5, 7]),
    },
}
DEFAULT = ("A", "noins_nopens_or_c57")


def _ins_work(d):
    return d["ins_essalud"].eq(1) | d["ins_eps"].eq(1) | d["ins_priv"].eq(1) | d["ins_ffaa"].eq(1)


def informal(d: pd.DataFrame, sector: str = DEFAULT[0], wage: str = DEFAULT[1]) -> pd.Series:
    """1 = empleo informal, 0 = formal, NA = no ocupado."""
    occ = d["ocu500"].eq(1)
    cat = d["cat_ocup"]
    sec_inf = VARIANTS["sector"][sector](d).fillna(False)
    unprotected = VARIANTS["wage"][wage](d).fillna(True)
    out = pd.Series(pd.NA, index=d.index, dtype="Int8")
    self_emp = cat.isin([1, 2])
    wage_w = cat.isin([3, 4, 6, 7])
    tfnr = cat.eq(5)
    out[occ & self_emp] = sec_inf[occ & self_emp].astype("Int8")
    out[occ & wage_w] = (sec_inf | unprotected)[occ & wage_w].astype("Int8")
    out[occ & tfnr] = 1
    return out


def fit(d: pd.DataFrame) -> pd.DataFrame:
    """Concordancia de cada variante con ocupinf (1 informal, 2 formal) entre ocupados."""
    occ = d[d["ocu500"].eq(1) & d["ocupinf_inei"].isin([1, 2])]
    truth = occ["ocupinf_inei"].eq(1).astype(int)
    w = occ["w500"]
    rows = []
    for s in VARIANTS["sector"]:
        for wg in VARIANTS["wage"]:
            pred = informal(occ, s, wg).astype(float)
            agree = (pred == truth)
            rows.append({"sector": s, "wage": wg,
                         "agree_unw": agree.mean(), "agree_w": (agree * w).sum() / w.sum(),
                         "rate_rule": (pred * w).sum() / w.sum(), "rate_inei": (truth * w).sum() / w.sum()})
    return pd.DataFrame(rows).sort_values("agree_w", ascending=False)
