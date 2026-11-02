import glob
import json
import pandas as pd
import pytest
from olp.config import OUT_DIR, SITE_DATA_DIR

LATEST = SITE_DATA_DIR / "latest"
pytestmark = pytest.mark.skipif(not (LATEST / "estimates.parquet").exists(), reason="bulk files not built")
HIDDEN = ["estimate", "se", "rse_pct", "ci_lo", "ci_hi", "population"]


@pytest.fixture(scope="module")
def df():
    return pd.read_parquet(LATEST / "estimates.parquet")


def test_suppressed_cells_are_blank_in_every_format(df):
    assert df.loc[df.grade == "S", HIDDEN].isna().all().all()
    csv = pd.read_csv(LATEST / "estimates.csv.gz", dtype={"key": str}, low_memory=False)
    assert len(csv) == len(df) and csv.loc[csv.grade == "S", HIDDEN].isna().all().all()
    dta = pd.read_stata(LATEST / "observatorio_laboral.dta", convert_categoricals=True)
    assert len(dta) == len(df) and dta.loc[dta.grade == "S", HIDDEN].isna().all().all()
    for f in glob.glob(str(LATEST / "por_*" / "*")):
        part = pd.read_csv(f, low_memory=False)
        assert part.loc[part.grade == "S", HIDDEN].isna().all().all()
    xl = pd.read_excel(LATEST / "observatorio_laboral.xlsx", sheet_name="estimates")
    assert xl.loc[xl.grade == "S", HIDDEN].isna().all().all()


def test_published_cells_keep_a_value(df):
    assert df.loc[df.grade != "S", "estimate"].notna().all()


def test_matches_internal_estimates_and_row_count(df):
    est = pd.read_parquet(OUT_DIR / "estimates.parquet")
    prov = pd.read_parquet(OUT_DIR / "estimates_prov.parquet")
    assert len(df) == len(est) + len(prov)
    a = est[(est.grade != "S") & est.category.isna()].merge(df[df.domain != "prov"], on=["year", "indicator", "domain", "key"], suffixes=("", "_b"))
    assert (a.est.round(3) - a.estimate).abs().max() < 1e-9


def test_matches_compendium(df):
    idx = json.load(open(SITE_DATA_DIR / "compendium_index.json"))
    checked = 0
    for t in idx["tables"]:
        c = pd.read_csv(SITE_DATA_DIR / t["file"], dtype={"row_key": str})
        if "estimate" not in c or "row_key" not in c:
            continue
        m = c.merge(df, left_on=["year", "domain", "row_key", "indicator", "category"], right_on=["year", "domain", "key", "indicator", "category"], suffixes=("", "_b"))
        assert len(m) == len(c), t["id"]
        assert (m.estimate.fillna(-1) - m.estimate_b.fillna(-1)).abs().max() < 1e-6, t["id"]
        checked += 1
    assert checked > 30


def test_matches_headline(df):
    h = json.load(open(SITE_DATA_DIR / "headline.json"))
    r = df[(df.indicator == "informality") & (df.domain == "national") & (df.year == h["year"])].iloc[0]
    assert round(r.estimate, 1) == h["kpis"]["informality"]["v"]
    assert r.method_note == "informality_rule_2024"


def test_manifest_covers_all_files():
    m = json.load(open(LATEST / "manifest.json"))
    assert {f["path"] for f in m["files"]} == {str(p.relative_to(LATEST)) for p in LATEST.rglob("*") if p.is_file() and p.name != "manifest.json"}
