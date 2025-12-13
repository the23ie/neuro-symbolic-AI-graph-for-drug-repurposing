# build_compound_disease_ids.py
# Python 3 compatible
# Extract compound and disease node IDs from DRKG using relation IDs only

import pickle

DATA_DIR = "data/drkg"

TRAIN_FILE = f"{DATA_DIR}/train.txt"
OUT_COMPOUND = f"{DATA_DIR}/compound_ids.pkl"
OUT_DISEASE = f"{DATA_DIR}/disease_ids.pkl"

# Identified Drug–Disease relation IDs from DRKG analysis
DRUG_DISEASE_REL_IDS = {99, 63, 86}

compound_nodes = set()
disease_nodes = set()

print("Reading train triples...")

with open(TRAIN_FILE) as f:
    for line in f:
        h, r, t = map(int, line.strip().split())
        if r in DRUG_DISEASE_REL_IDS:
            compound_nodes.add(h)
            disease_nodes.add(t)

print("Compounds:", len(compound_nodes))
print("Diseases:", len(disease_nodes))

with open(OUT_COMPOUND, "wb") as f:
    pickle.dump(list(compound_nodes), f)

with open(OUT_DISEASE, "wb") as f:
    pickle.dump(list(disease_nodes), f)

print("Saved compound_ids.pkl and disease_ids.pkl")
