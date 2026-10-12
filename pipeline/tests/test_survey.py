import numpy as np, pandas as pd
from olp.survey import Design


def toy():
    # 2 strata × 3 PSUs × 4 obs
    rows = []
    rng = np.random.default_rng(1)
    for s in range(2):
        for p in range(3):
            for i in range(4):
                rows.append({"stratum": f"s{s}", "psu": f"{s}{p}", "w500": 1 + s, "y": float(rng.integers(0, 2))})
    return pd.DataFrame(rows)


def test_ratio_matches_hand_computation():
    d = toy(); D = Design(d)
    y = d.y.to_numpy(float); x = np.ones(len(d)); m = np.ones(len(d), bool)
    e = D.ratio(y, x, m)
    w = d.w500.to_numpy(float); R = (w * y).sum() / w.sum()
    z = w * (y - R) / w.sum()
    d["z"] = z
    Z = d.groupby(["stratum", "psu"]).z.sum().reset_index()
    var = 0.0
    for s, g in Z.groupby("stratum"):
        nh = len(g); var += nh / (nh - 1) * ((g.z - g.z.mean()) ** 2).sum()
    assert abs(e.est - R) < 1e-12 and abs(e.se - np.sqrt(var)) < 1e-12


def test_quantile_and_grade():
    d = toy(); d["y"] = np.arange(len(d), dtype=float); D = Design(d)
    e = D.quantile(d.y.to_numpy(float), np.ones(len(d), bool), 0.5)
    assert 8 <= e.est <= 16 and e.lo <= e.est <= e.hi
    assert e.grade == "S"  # n < 30


def test_diff_zero_for_identical_groups():
    d = toy(); D = Design(d)
    y = d.y.to_numpy(float); x = np.ones(len(d)); m = np.ones(len(d), bool)
    e = D.diff(y, x, m, m)
    assert abs(e.est) < 1e-12 and e.se < 1e-12
