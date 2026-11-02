"""Shapefile de departamentos → TopoJSON simplificado con id = ubigeo2."""
import geopandas as gpd
import pandas as pd
import shapely
import topojson as tp
from shapely.geometry.polygon import orient
from .config import SHAPEFILE, PROV_SHP, CONFIG_DIR, SITE_DATA_DIR


def _clockwise(geom):
    """d3 reads clockwise exterior rings as the inside of a shape."""
    if geom.geom_type == "Polygon":
        return orient(geom, -1)
    return shapely.MultiPolygon([orient(p, -1) for p in geom.geoms])


def build(tolerance=0.01):
    g = gpd.read_file(SHAPEFILE)[["departamen", "region_nat", "geometry"]]
    cw = pd.read_csv(CONFIG_DIR / "dept_crosswalk.csv", dtype=str)
    cw = cw[cw.name_shapefile.notna() & (cw.name_shapefile != "")]
    g = g.merge(cw[["ubigeo2", "name", "name_shapefile"]], left_on="departamen", right_on="name_shapefile", how="left")
    assert g.ubigeo2.notna().all(), g[g.ubigeo2.isna()].departamen.tolist()
    g = g[["ubigeo2", "name", "region_nat", "geometry"]].rename(columns={"ubigeo2": "id"})
    # Simplify the coverage as a whole so neighbours keep one shared border.
    g["geometry"] = shapely.coverage_simplify(g.geometry.make_valid().values, tolerance)
    g["geometry"] = g.geometry.map(_clockwise)
    topo = tp.Topology(g, prequantize=1e5, topology=True, toposimplify=False)
    out = SITE_DATA_DIR / "departamentos.topo.json"
    out.write_text(topo.to_json())
    return out


def build_provinces(tolerance=0.01):
    """Shapefile provincial → provincias.topo.json (id = ubigeo 4 dígitos) y DataFrame de nombres."""
    g = gpd.read_file(PROV_SHP)
    cols = {c.lower(): c for c in g.columns}
    idc = next(cols[c] for c in cols if c in ("idprov", "ubigeo", "ccpp", "cod_prov", "id_prov", "idprovincia"))
    nmc = next(cols[c] for c in cols if c in ("provincia", "nombprov", "nom_prov", "nombre"))
    g["id"] = g[idc].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(4).str[:4]
    g["name"] = g[nmc].astype(str).str.title()
    g = g[["id", "name", "geometry"]].dissolve(by="id", aggfunc="first").reset_index()
    if g.crs and g.crs.to_epsg() != 4326:
        g = g.to_crs(4326)
    g["geometry"] = shapely.coverage_simplify(g.geometry.make_valid().values, tolerance)
    g["geometry"] = g.geometry.map(_clockwise)
    topo = tp.Topology(g, prequantize=1e5, topology=True, toposimplify=False)
    (SITE_DATA_DIR / "provincias.topo.json").write_text(topo.to_json())
    names = pd.DataFrame({"ubigeo4": g["id"], "name": g["name"], "dept": g["id"].str[:2]})
    names.to_csv(CONFIG_DIR / "prov_names.csv", index=False)
    return names
