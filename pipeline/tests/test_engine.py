import numpy as np, pandas as pd
import pytest
from olp.engine import run_year
from olp.survey import Design, Estimate
from olp.models import cell_from
from olp import validate


def frame(n=6000, seed=7):
    rng = np.random.default_rng(seed)
    d = pd.DataFrame({"stratum": rng.integers(0, 6, n).astype(str), "psu": rng.integers(0, 80, n).astype(str), "w500": rng.uniform(50, 150, n),
                      "sex": rng.integers(1, 3, n), "pet": 1})
    d["pea"] = (rng.random(n) < np.where(d.sex == 1, 0.8, 0.6)).astype(int)
    d["ocupado"] = d.pea * (rng.random(n) < 0.95)
    d["desocupado"] = d.pea - d.ocupado
    d["has_income"] = d.ocupado
    d["inc_real_pos"] = np.where(d.ocupado == 1, rng.lognormal(7, 0.6, n) * np.where(d.sex == 2, 0.7, 1.0), np.nan)
    d["hours"] = np.where(d.ocupado == 1, rng.normal(42, 10, n), np.nan)
    d["status6"] = np.where(d.ocupado == 1, rng.integers(1, 4, n), np.nan)
    return d


@pytest.fixture(scope="module")
def est():
    return run_year(frame(), 2024, domains=["national", "sex"], indicators=["lfpr", "ur", "mean_inc_real", "median_inc_real", "hours_mean", "status_dist", "gap_lfpr", "gap_inc"])


def one(est, ind, dom="national", key="all"):
    r = est[(est.indicator == ind) & (est.domain == dom) & (est.key == key) & est.category.isna()]
    assert len(r) == 1
    return r.iloc[0]


def test_prop_matches_weighted_share(est):
    d = frame()
    assert one(est, "lfpr").est == pytest.approx(100 * (d.w500 * d.pea).sum() / d.w500.sum())
    assert one(est, "ur").est == pytest.approx(100 * (d.w500 * d.desocupado).sum() / (d.w500 * d.pea).sum())
    assert one(est, "lfpr").grade == "A" and 0 < one(est, "lfpr").se < 2


def test_mean_and_median_are_ordered_for_lognormal(est):
    assert one(est, "mean_inc_real").est > one(est, "median_inc_real").est > 0
    assert one(est, "median_inc_real").lo <= one(est, "median_inc_real").est <= one(est, "median_inc_real").hi


def test_dist_categories_sum_to_100(est):
    r = est[(est.indicator == "status_dist") & (est.domain == "national")]
    assert sorted(r.category) == [1, 2, 3] and r.est.sum() == pytest.approx(100)


def test_gap_is_difference_of_domain_rates(est):
    assert one(est, "gap_lfpr").est == pytest.approx(one(est, "lfpr", "sex", "1").est - one(est, "lfpr", "sex", "2").est)
    assert one(est, "gap_lfpr").grade == "A"


def test_gap_inc_is_published_with_a_standard_error(est):
    g = one(est, "gap_inc")
    assert g.est == pytest.approx(one(est, "median_inc_real", "sex", "2").est / one(est, "median_inc_real", "sex", "1").est)
    assert 0.6 < g.est < 0.8 and 0 < g.se < 0.05 and g.grade == "A"
    assert g.lo < g.est < g.hi


def test_quantile_ratio_small_cell_is_suppressed():
    d = frame(40); D = Design(d)
    y = d.inc_real_pos.to_numpy(float)
    e = D.quantile_ratio(y, (d.sex == 2).to_numpy(), (d.sex == 1).to_numpy())
    assert e.n < 30 and e.grade == "S"


def test_differences_are_graded_by_n_not_rse():
    assert Estimate(0.001, 0.5, 5000, 0.0, kind="diff").grade == "A"   # RSE enorme, n grande
    assert cell_from(0.001, 0.5, 5000)["g"] == "A" and cell_from(1.0, 0.1, 50)["g"] == "B" and cell_from(1.0, 0.1, 10)["g"] == "S"


def test_validation_gate_flags_new_failures_and_missing_estimates():
    known = validate.load_yaml("validation_known.yml")["known"][0]
    df = pd.DataFrame([
        {"year": known["year"], "indicator": known["indicator"], "domain": known["domain"], "observatorio": 1.0, "ok": False},
        {"year": 1999, "indicator": "lfpr", "domain": "national", "observatorio": 1.0, "ok": True},
        {"year": 1999, "indicator": "ur", "domain": "national", "observatorio": 1.0, "ok": False},
        {"year": known["year"], "indicator": known["indicator"], "domain": known["domain"], "observatorio": np.nan, "ok": False},
    ])
    assert validate.unexpected(df).index.tolist() == [2, 3]


def test_gini_known_values():
    d = frame(2000); D = Design(d); m = np.ones(len(d), bool)
    assert D.gini(np.full(len(d), 500.0), m).est == pytest.approx(0, abs=1e-12)        # todos ganan lo mismo
    d2 = d.assign(w500=1.0); D2 = Design(d2); y = np.where(np.arange(len(d2)) % 2 == 0, 0.0, 100.0)
    assert D2.gini(y, m).est == pytest.approx(0.5)                                      # la mitad gana todo
    g = D.gini(d.inc_real_pos.fillna(1).to_numpy(float), m)
    assert 0 < g.est < 1 and 0 < g.se < 0.05 and g.grade == "A"
