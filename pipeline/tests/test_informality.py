from olp.build_person import load_person
from olp.informality import fit, DEFAULT


def test_agreement_2023():
    f = fit(load_person(2023))
    best = f[(f.sector == DEFAULT[0]) & (f.wage == DEFAULT[1])].iloc[0]
    assert best.agree_w >= 0.98
