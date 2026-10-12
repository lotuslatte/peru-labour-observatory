import pytest
from olp.config import YEARS
from olp.harmonise import resolve, module_spec
from olp.files import enaho_file
import pyreadstat


@pytest.mark.parametrize("year", YEARS)
def test_all_canonical_vars_resolve(year):
    for module in ("m02", "m03", "m04", "m05", "m34"):
        p = enaho_file(module, year)
        reader = pyreadstat.read_sav if p.suffix.lower() == ".sav" else pyreadstat.read_dta
        _, meta = reader(str(p), metadataonly=True)
        cols = {c.lower() for c in meta.column_names}
        mapping, optional = resolve(module, year)
        missing = [src for src in mapping.values() if src not in cols and src not in optional]
        assert not missing, (module, year, missing)
