import json

entities_file = "data/drkg/embed/entities.tsv"
out_json = "data/drkg/entity2id.json"

entity2id = {}

with open(entities_file, "r") as f:
    for idx, line in enumerate(f):
        entity = line.strip()
        if entity:
            entity2id[entity] = idx

with open(out_json, "w") as f:
    json.dump(entity2id, f, indent=2)

print(f"Wrote {len(entity2id)} entities → {out_json}")
