"""Run every indicator recipe in Stata, R and Python on the headline-year microdata and compare with estimates.

Usage: python pipeline/scripts/09_check_recipes.py [indicator ...] [--lang stata,r,python]
Writes pipeline/out/recipes_check.csv and exits non-zero if any point estimate differs beyond tolerance.
"""
import argparse
import concurrent.futures as cf
import re
import subprocess
import sys
import tempfile
from pathlib import Path
import pandas as pd
from olp.config import ENAHO_DIR, HEADLINE_YEAR as Y, OUT_DIR
from olp.engine import IND
from olp.aggregate import fichas
from olp import recipes

STATA = "/opt/Stata/stata14/stata"
FILES = {f"enaho01a-{Y}-500.dta": "modulo_05", f"enaho01a-{Y}-300.dta": "modulo_03",
         f"enaho01a-{Y}-400.dta": "modulo_04", f"sumaria-{Y}.dta": "modulo_34"}
TOL = {"%": 0.01, "pp": 0.01, "S/": 0.5, "S/h": 0.01, "h": 0.01, "ratio": 0.001}
TAIL = {
    "stata": ("capture confirm matrix est\nif _rc == 0 {\n  forvalues i = 1/`=colsof(est)' {\n    display \"OLPEST \" %20.10g est[1, `i']\n  }\n}\n"
              "else display \"OLPEST \" %20.10g est\n"),
    "r": 'cat("OLPEST", format(est, digits = 12), "\\n")\n',
    "python": 'print("OLPEST", *(est.values() if isinstance(est, dict) else [est]))\n',
}
EXT = {"stata": "do", "r": "R", "python": "py"}


def data_dir(tmp: Path) -> Path:
    d = tmp / "enaho"
    d.mkdir()
    for f, mod in FILES.items():
        src = next((ENAHO_DIR / mod).glob(f), None) or next(p for p in (ENAHO_DIR / mod).iterdir() if p.name.lower() == f)
        (d / f).symlink_to(src)
    return d


def run(lang, code, work: Path, data: Path):
    code = code.replace('cd "."', f'cd "{data}"').replace('ruta <- "."', f'ruta <- "{data}"').replace('RUTA = "."', f'RUTA = "{data}"')
    f = work / f"recipe.{EXT[lang]}"
    f.write_text(code + TAIL[lang], encoding="utf-8")
    if lang == "stata":
        p = subprocess.run([STATA, "-b", "do", f.name], cwd=work, capture_output=True, text=True, timeout=900)
        out = (work / "recipe.log").read_text(errors="replace")
    elif lang == "r":
        p = subprocess.run(["Rscript", f.name], cwd=work, capture_output=True, text=True, timeout=900)
        out = p.stdout + p.stderr
    else:
        p = subprocess.run([sys.executable, "-I", f.name], cwd=work, capture_output=True, text=True, timeout=900)
        out = p.stdout + p.stderr
    vals = [float(x) for line in out.splitlines() if line.startswith("OLPEST") for x in line.split()[1:]]
    err = "" if vals else out[-1500:]
    if lang == "stata" and re.search(r"^r\(\d+\);", out, re.M):
        err = out[-1500:]
    return vals, err


def published(est, ind):
    t = IND[ind]["type"]
    r = est[(est.indicator == ind) & (est.domain == "national") & (est.year == Y)]
    if t == "dist":
        return r.sort_values("category").est.tolist()
    return r[r.category.isna()].est.tolist()


def check(ind, lang, est, data, root):
    name = fichas.DOCS["indicators"][ind]["name"]
    own = fichas.own_vars(ind)
    code = recipes.build(ind, name, fichas.expand(own) + [v for v in own if v not in fichas.DERIVED])[lang]
    work = Path(tempfile.mkdtemp(dir=root))
    vals, err = run(lang, code, work, data)
    pub = published(est, ind)
    u = recipes.unit_of(ind)
    diff = max((abs(a - b) for a, b in zip(vals, pub)), default=float("nan")) if len(vals) == len(pub) else float("nan")
    ok = len(vals) == len(pub) and diff <= TOL.get(u, 0.01)
    return {"indicator": ind, "lang": lang, "ok": ok, "max_abs_diff": diff, "recipe": vals[:3], "published": pub[:3], "error": err.strip()[-600:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("indicators", nargs="*")
    ap.add_argument("--lang", default="stata,r,python")
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    inds = a.indicators or list(IND)
    langs = a.lang.split(",")
    est = pd.read_parquet(OUT_DIR / "estimates.parquet")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = data_dir(root)
        with cf.ThreadPoolExecutor(a.jobs) as ex:
            rows = list(ex.map(lambda p: check(p[0], p[1], est, data, root), [(i, l) for i in inds for l in langs]))
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "recipes_check.csv", index=False)
    bad = df[~df.ok]
    print(f"{len(df) - len(bad)} of {len(df)} recipes match")
    for _, r in bad.iterrows():
        print(f"FAIL {r.indicator} [{r.lang}] diff={r.max_abs_diff} recipe={r.recipe} published={r.published}\n  {r.error[-400:]}")
    sys.exit(1 if len(bad) else 0)


if __name__ == "__main__":
    main()
