import numpy as np, pandas as pd
from olp.survey import Design
from olp.design_matrix import Spec
from olp.decompose import oaxaca, shift_share


def frame(n=4000, seed=3):
    rng = np.random.default_rng(seed)
    d = pd.DataFrame({"stratum": rng.integers(0, 5, n).astype(str), "psu": rng.integers(0, 60, n).astype(str), "w500": rng.uniform(1, 3, n), "g": rng.integers(1, 3, n), "e": rng.integers(1, 4, n)})
    d["y"] = 1 + 0.5 * d.e + 0.3 * (d.g == 2) + rng.normal(size=n)
    d["one"] = 1
    return d


def test_oaxaca_identity():
    d = frame(); D = Design(d)
    r = oaxaca(D, d, "y", "g", 2, 1, Spec([{"var": "e", "contrast": "dev"}]), d.one.to_numpy() == 1, R=20)
    assert abs(r["gap"]["v"] - (r["explained"]["v"] + r["unexplained"]["v"])) < 1e-10
    assert abs(sum(b["explained"]["v"] for b in r["by_var"]) - r["explained"]["v"]) < 1e-10


def test_shift_share_identity():
    d0 = frame(seed=1); d1 = frame(seed=2); d1["y"] = (d1.y > 2).astype(float); d0["y"] = (d0.y > 2).astype(float)
    r = shift_share(Design(d0), d0, Design(d1), d1, "y", "e", d0.one == 1, d1.one == 1, R=10)
    assert abs(r["total"]["v"] - (r["composition"]["v"] + r["rate"]["v"])) < 1e-10
