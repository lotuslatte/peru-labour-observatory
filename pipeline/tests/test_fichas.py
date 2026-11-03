"""Indicator pages: every indicator is documented, comparability covers every year, no suppressed value leaks."""
import json
import pytest
from olp.config import SITE_DATA_DIR, YEARS, load_yaml
from olp.engine import IND

FICHAS = SITE_DATA_DIR / "fichas"
pytestmark = pytest.mark.skipif(not (FICHAS / "index.json").exists(), reason="fichas not built")
BREAKS = load_yaml("series_breaks.yml")["breaks"]


def load(i):
    return json.loads((FICHAS / f"{i}.json").read_text(encoding="utf-8"))


def cells(obj):
    """Every estimate cell in a nested structure."""
    if isinstance(obj, dict):
        if "g" in obj and "v" in obj:
            yield obj
        for v in obj.values():
            yield from cells(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from cells(v)


def test_index_lists_every_indicator():
    idx = json.loads((FICHAS / "index.json").read_text(encoding="utf-8"))
    assert [d["id"] for d in idx["indicators"]] == list(IND)


@pytest.mark.parametrize("i", list(IND))
def test_each_indicator_is_documented(i):
    f = load(i)
    assert f["def"] and f["name"] and f["group"]
    assert len(f["measure"]) >= 2 and all(text for _, text in f["measure"])
    assert f["vars"] and all(v["enaho"] and v["module"] for v in f["vars"])
    assert [c["year"] for c in f["comparability"]] == YEARS
    assert len(f["national"]) == (len(YEARS) if f["type"] != "dist" else len(IND[i]["labels_es"]))


@pytest.mark.parametrize("i", list(IND))
def test_no_suppressed_value(i):
    for c in cells(load(i)):
        assert c["g"] != "S" or c["v"] is None


def test_breaks_mark_their_first_year_and_sources():
    for b in BREAKS:
        for i in b["indicators"]:
            comp = {c["year"]: c for c in load(i)["comparability"]}
            assert comp[b["year"]]["status"] == "break"
            assert comp[b["year"] - 1]["source"] == b["before_es"]
            assert comp[b["year"]]["source"] == b["after_es"]


def test_missing_years_are_not_comparable():
    comp = {c["year"]: c["status"] for c in load("mig_life")["comparability"]}
    assert all(comp[y] == "nd" for y in YEARS if y < 2018)
