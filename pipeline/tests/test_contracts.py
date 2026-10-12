import json
from olp.config import SITE_DATA_DIR


def _cell_ok(c):
    assert set(c) >= {"v", "g", "n"}
    assert c["g"] in ("A", "B", "S")
    if c["g"] == "S":
        assert c["v"] is None
    else:
        assert isinstance(c["v"], (int, float))


def test_headline():
    h = json.load(open(SITE_DATA_DIR / "headline.json"))
    for k in ("lfpr", "epr", "ur", "informality"):
        _cell_ok(h["kpis"][k]); assert h["kpis"][k]["g"] == "A"


def test_atlas_and_profiles():
    a = json.load(open(SITE_DATA_DIR / "atlas_regions.json"))
    assert len(a["regions"]) == 27
    for r in a["regions"]:
        for d in a["dims"]:
            _cell_ok(r["values"][d["id"]])
        p = json.load(open(SITE_DATA_DIR / "profiles" / f"{r['id']}.json"))
        assert p["id"] == r["id"] and len(p["trend"]["lfpr"]) == 11
