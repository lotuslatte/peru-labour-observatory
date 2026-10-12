"""Construye el archivo persona-año: base módulo 500 (PET 14+) + m02/m03/m04/sumaria."""
import numpy as np
import pandas as pd
from .config import OUT_DIR, PET_AGE
from .harmonise import load_module, apply_recodes, KEYS


def build(year: int, write: bool = True) -> pd.DataFrame:
    m05 = load_module("m05", year)
    n0 = len(m05)
    m05["year"] = year
    for c in m05.columns:
        if c not in KEYS + ["ubigeo", "year"]:
            m05[c] = pd.to_numeric(m05[c], errors="coerce")
    m02 = load_module("m02", year)
    m03 = load_module("m03", year)
    m04 = load_module("m04", year)
    m34 = load_module("m34", year)
    for d in (m02, m03, m04, m34):
        for c in d.columns:
            if c not in KEYS + ["ubigeo"]:
                d[c] = pd.to_numeric(d[c], errors="coerce")
    for d, name in ((m02, "m02"), (m03, "m03"), (m04, "m04")):
        assert not d.duplicated(KEYS).any(), f"{name} {year}: duplicate person keys"
    assert not m34.duplicated(KEYS[:3]).any()
    df = (m05.merge(m02, on=KEYS, how="left")
             .merge(m03, on=KEYS, how="left")
             .merge(m04, on=KEYS, how="left")
             .merge(m34, on=KEYS[:3], how="left"))
    assert len(df) == n0
    # member of household & PET
    df = df[(df["member"].fillna(1) == 1)]
    df["age"] = df["age"].fillna(df["age_m02"])
    df["sex"] = df["sex"].fillna(df["sex_m02"])
    df = df[df["age"] >= PET_AGE].copy()
    df = df[df["w500"].notna() & (df["w500"] > 0)].copy()
    df["dept"] = df["ubigeo"].str[:2]
    df["prov"] = df["ubigeo"].str[:4]
    df["educ_raw"] = df["educ_raw"].fillna(df["educ_raw_m05"])
    df = apply_recodes(df)
    df["psu"] = df["conglome"]
    df["stratum"] = df["dept"] + "-" + df["estrato"].astype("Int64").astype(str)
    if write:
        OUT_DIR.mkdir(exist_ok=True)
        df.to_parquet(OUT_DIR / f"person_{year}.parquet", index=False)
    return df


def load_person(year: int) -> pd.DataFrame:
    return pd.read_parquet(OUT_DIR / f"person_{year}.parquet")
