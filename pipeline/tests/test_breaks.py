"""Comparisons across a declared method break are never significant."""
from olp.aggregate.common import crossed_break
from olp.aggregate.narrative import delta


def cell(est):
    return {"est": est, "se": 0.1, "grade": "A"}


def test_crossed_break_detects_only_spanning_comparisons():
    assert crossed_break("informality", 2023, 2024) == "informality_rule_2024"
    assert crossed_break("formality", 2014, 2024) == "informality_rule_2024"
    assert crossed_break("informality", 2022, 2023) is None
    assert crossed_break("ur", 2014, 2024) is None


def test_delta_across_break_is_flagged_and_not_significant():
    out = delta(cell(73.0), cell(70.0), brk="informality_rule_2024")
    assert out["d"] == 3.0
    assert out["sig"] is False
    assert out["break"] == "informality_rule_2024"


def test_delta_without_break_keeps_significance():
    out = delta(cell(73.0), cell(70.0))
    assert out["sig"] is True
    assert "break" not in out
