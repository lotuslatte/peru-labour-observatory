"""Índice y hashes de public/data; va al final porque geo, modelos y provincias escriben ahí después de 04."""
from olp.aggregate import index_json
print("index", index_json.build())
