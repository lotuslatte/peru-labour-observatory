import pandas as pd, geopandas as gpd
from olp.aggregate import provinces
from olp.derive import derive
from olp.config import SHAPEFILE, CONFIG_DIR
from olp.geo import build_provinces
est = provinces.run(derive)
names = build_provinces()  # también devuelve DataFrame ubigeo4/name
ids = [i["id"] for i in provinces.CFG["indicators"]]
print(provinces.build(est, ids, names))
