import json
import pytest
from olp.config import SITE_DATA_DIR

PATH = SITE_DATA_DIR / "territorios.json"
pytestmark = pytest.mark.skipif(not PATH.exists(), reason="territorios.json not built")


def load():
    return json.loads(PATH.read_text()), json.loads((SITE_DATA_DIR / "atlas_provincias.json").read_text())


def test_gaps_only_use_published_cells():
    t, a = load()
    names = {(r["parent"], r["name"], d["id"]): r["values"][d["id"]] for r in a["regions"] for d in a["dims"] if d["id"] in r["values"]}
    for ind, rows in t["gaps"].items():
        for x in rows:
            for end in ("min", "max"):
                c = names[(x["dept"], x[end]["name"], ind)]
                assert c["g"] != "S" and c["v"] == x[end]["v"]


def test_analysis_excludes_blank_cells():
    t, a = load()
    regs = {r["id"]: r for r in a["regions"]}
    for pid in t["typologies"]["province"]:
        assert all(regs[pid]["values"][i]["v"] is not None for i in t["typologies"]["dims"])
    for ind, s in t["spatial"].items():
        assert all(regs[pid]["values"][ind]["v"] is not None for pid in s["cluster"])


def test_groups_are_named_and_cover_population():
    t, _ = load()
    groups = t["typologies"]["groups"]
    assert all(g.get("name") for g in groups) and abs(sum(g["pop_share"] for g in groups) - 100) < 0.5
