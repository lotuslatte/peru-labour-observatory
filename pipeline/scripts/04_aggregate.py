from olp.aggregate.common import load_estimates
from olp.aggregate import index_json, headline, atlas, trends, profiles, compendium, meta, digest
from olp import validate
est = load_estimates()
print("headline", headline.build(est))
print("atlas", atlas.build(est))
print("trends", trends.build(est))
print("profiles", len(profiles.build(est)))
v = validate.run(est)
print("validation", v.ok.mean().round(3), "ok share")
print("compendium", len(compendium.build(est)), "tables")
print("meta", meta.build(est))
print("digest", digest.build(est))

print("index", index_json.build())
