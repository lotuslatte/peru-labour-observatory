"""Skip tests that need local inputs (ENAHO microdata, pipeline/out) when those are absent."""
import pytest
from olp.config import ENAHO_DIR, OUT_DIR


def pytest_configure(config):
    config.addinivalue_line("markers", "needs_microdata: reads the raw ENAHO mirror")
    config.addinivalue_line("markers", "needs_person: reads pipeline/out/person_*.parquet")


def pytest_collection_modifyitems(config, items):
    have = {"needs_microdata": ENAHO_DIR.is_dir(), "needs_person": any(OUT_DIR.glob("person_*.parquet"))}
    for item in items:
        for mark, ok in have.items():
            if mark in item.keywords and not ok:
                item.add_marker(pytest.mark.skip(reason=f"{mark}: input not available on this machine"))
