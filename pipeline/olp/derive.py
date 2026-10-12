"""Banderas derivadas a nivel persona (INEI: PET 14+, PEA = ocupados + desocupados abiertos)."""
import numpy as np
import pandas as pd
from .config import CONFIG_DIR, YOUTH
from .informality import informal

_IPC = pd.read_csv(CONFIG_DIR / "ipc_lima_2014_2024.csv", comment="#").set_index("year")["deflator_to_2024"]
# Remuneración mínima vital (S/ mensual, vigente la mayor parte del año) — proxy transparente del IMR de INEI
RMV = {2014: 750, 2015: 750, 2016: 850, 2017: 850, 2018: 930, 2019: 930, 2020: 930, 2021: 930,
       2022: 1025, 2023: 1025, 2024: 1025}
SECTOR9 = {  # CIIU rev4 secciones -> 9 sectores
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 4, "F": 5, "G": 6, "H": 7, "J": 7,
    "I": 8, "K": 9, "L": 9, "M": 9, "N": 9, "O": 9, "P": 9, "Q": 9, "R": 8, "S": 8, "T": 8, "U": 9,
}
SECTOR9_LABELS = {1: "Agropecuario y pesca", 2: "Minería", 3: "Manufactura", 4: "Electricidad y agua",
                  5: "Construcción", 6: "Comercio", 7: "Transporte y comunicaciones",
                  8: "Alojamiento, restaurantes y otros servicios", 9: "Servicios profesionales, públicos y sociales"}


def ciiu4_section(code: pd.Series) -> pd.Series:
    c = pd.to_numeric(code, errors="coerce")
    div = (c // 100).where(c >= 1000, c // 10)  # 4-digit -> division (first two digits)
    div = div.where(div.notna(), np.nan)
    bins = [(1, 3, "A"), (5, 9, "B"), (10, 33, "C"), (35, 35, "D"), (36, 39, "E"), (41, 43, "F"), (45, 47, "G"),
            (49, 53, "H"), (55, 56, "I"), (58, 63, "J"), (64, 66, "K"), (68, 68, "L"), (69, 75, "M"), (77, 82, "N"),
            (84, 84, "O"), (85, 85, "P"), (86, 88, "Q"), (90, 93, "R"), (94, 96, "S"), (97, 98, "T"), (99, 99, "U")]
    out = pd.Series(np.nan, index=code.index, dtype=object)
    for lo, hi, s in bins:
        out[(div >= lo) & (div <= hi)] = s
    return out


def derive(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    y = int(d["year"].iloc[0])
    occ = d["ocu500"].eq(1)
    d["pet"] = 1
    d["pea"] = d["ocu500"].isin([1, 2]).astype("Int8")
    d["ocupado"] = occ.astype("Int8")
    d["desocupado"] = d["ocu500"].eq(2).astype("Int8")
    d["youth"] = d["age"].between(*YOUTH).astype("Int8")
    d["age4"] = pd.cut(d["age"], [13, 24, 44, 64, 200], labels=[1, 2, 3, 4]).astype("Int8")
    # informality
    # Informalidad: flag oficial INEI (ocupinf) cuando existe (2014–2023); regla del Observatorio cuando no (2024).
    d["informal_rule"] = informal(d)
    if d["ocupinf_inei"].notna().any():
        d["informal"] = d["ocupinf_inei"].map({1: 1, 2: 0}).astype("Int8").where(occ)
        d["informal_source"] = "inei"
    else:
        d["informal"] = d["informal_rule"]
        d["informal_source"] = "rule"
    d["formal"] = (1 - d["informal"]).astype("Int8")
    d["informal_in_sector"] = pd.Series(pd.NA, index=d.index, dtype="Int8")
    d.loc[occ, "informal_in_sector"] = (d.loc[occ, "emplpsec_inei"].eq(1)).astype("Int8") if d["emplpsec_inei"].notna().any() \
        else (d.loc[occ, "informal"].eq(1) & d.loc[occ, "sunat_reg"].eq(3)).astype("Int8")
    # hours
    # Horas normales semanales (todas las ocupaciones): si la semana pasada fue normal (p519==1) → p513t+p518;
    # si no → horas normales declaradas/imputadas (i520, p520).
    lastweek = d["hours_lastweek_main"].fillna(0) + d["hours_sec"].fillna(0)
    usual = d["hours_usual"].where(d["hours_usual"].notna(), d["hours_usual_raw"])
    h = np.where(d["normal_hours"].eq(2) & usual.notna(), usual, lastweek)
    d["hours"] = pd.Series(h, index=d.index).where(occ)
    d["hours_lt35"] = (d["hours"] < 35).astype("Int8").where(occ)
    d["hours_le48"] = (d["hours"] <= 48).astype("Int8").where(occ)
    d["hours_ge60"] = (d["hours"] >= 60).astype("Int8").where(occ)
    d["subemp_hours"] = ((d["hours"] < 35) & d["wants_more"].eq(1) & d["avail_more"].eq(1)).astype("Int8").where(occ)
    # income (monthly, real 2024 soles)
    # Ingreso proveniente del trabajo (definición INEI, reproduce sus tablas oficiales): monetario + especie + autoconsumo + extraordinarios
    INC_VARS = ["inc_main_annual", "inc_main_inkind", "inc_self_annual", "inc_self_autoconsumo",
                "inc_sec_annual", "inc_sec_inkind", "inc_sec_self", "inc_sec_autoconsumo", "inc_extra_annual"]
    inc = d[INC_VARS].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1) / 12
    d["inc_month_nom"] = inc.where(occ)
    d["inc_month_real"] = (inc * float(_IPC.loc[y])).where(occ)
    d["has_income"] = (d["inc_month_nom"] > 0).astype("Int8").where(occ)
    d["inc_real_pos"] = d["inc_month_real"].where(d["inc_month_nom"] > 0)
    d["subemp_income"] = ((d["subemp_hours"].eq(0)) & (d["inc_month_nom"] < RMV[y]) & d["cat_ocup"].ne(5)).astype("Int8").where(occ)
    d["adecuado"] = ((d["subemp_hours"].eq(0)) & (d["subemp_income"].eq(0))).astype("Int8").where(occ)
    # status & protection
    d["wage_worker"] = d["cat_ocup"].isin([3, 4, 6]).astype("Int8").where(occ)
    d["self_emp"] = d["cat_ocup"].eq(2).astype("Int8").where(occ)
    d["tfnr"] = d["cat_ocup"].eq(5).astype("Int8").where(occ)
    d["employer"] = d["cat_ocup"].eq(1).astype("Int8").where(occ)
    ww = occ & d["wage_worker"].eq(1)
    d["contract_any"] = d["contract"].ne(7).astype("Int8").where(ww)
    d["contract_indef"] = d["contract"].eq(1).astype("Int8").where(ww)
    d["pension"] = d["pension_none"].ne(5).astype("Int8").where(occ)
    ins = d[["ins_essalud", "ins_priv", "ins_eps", "ins_ffaa", "ins_sis", "ins_univ", "ins_other1", "ins_other"]].eq(1).any(axis=1)
    d["seguro"] = ins.astype("Int8").where(occ)
    d["essalud"] = d["ins_essalud"].eq(1).astype("Int8").where(occ)
    d["firm_small"] = d["firm_size"].eq(1).astype("Int8").where(occ)
    d["secondary_job"] = d["cat_ocup_sec"].notna().astype("Int8").where(occ)
    d["sector9"] = ciiu4_section(d["ciiu4"]).map(SECTOR9).astype("Int8").where(occ)
    d["status6"] = d["cat_ocup"].replace({7: 6}).astype("Int8").where(occ)
    # NEET
    d["neet"] = ((~occ) & d["attends"].ne(1)).astype("Int8").where(d["youth"].eq(1))
    # migration
    cur = d["dept"]
    r5 = d["res5_ubigeo"].astype(str).str.zfill(6)
    d["mig_5y"] = (d["res5_same"].eq(2) & (r5.str[:2] != cur)).astype("Int8").where(d["res5_same"].isin([1, 2]))
    if d["birth_same"].notna().any():
        b = d["birth_ubigeo"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
        d["mig_life"] = (d["birth_same"].eq(2) & (b.str[:2] != cur)).astype("Int8").where(d["birth_same"].isin([1, 2]))
    else:
        d["mig_life"] = pd.Series(pd.NA, index=d.index, dtype="Int8")
    d["mig2"] = d["mig_5y"].map({0: 1, 1: 2}).astype("Int8")
    d["lima"] = np.select([d["prov"].eq("1501") | d["dept"].eq("07"), d["dept"].eq("15")], ["15M", "15R"], None)
    return d
