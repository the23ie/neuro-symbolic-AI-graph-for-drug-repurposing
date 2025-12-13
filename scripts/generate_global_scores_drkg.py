import json
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# Load embeddings + mapping
emb = np.load("embeddings.npy")
with open("entity2id.json") as f:
    node2id = json.load(f)

# Correct DRKG prefixes
drugs = [n for n in node2id if n.startswith("Compound::")]
diseases = [n for n in node2id if n.startswith("Disease::")]

print(f"Found {len(drugs)} drugs, {len(diseases)} diseases")

# Convert node names → embedding indices
drug_ids = [node2id[n] for n in drugs]
disease_ids = [node2id[n] for n in diseases]

# Safety check
if len(drug_ids) == 0 or len(disease_ids) == 0:
    raise ValueError(
        "ERROR: No drugs or diseases found. Check entity prefixes."
    )

# Slice embeddings
drug_emb = emb[drug_ids]
disease_emb = emb[disease_ids]

# Compute cosine similarity matrix
scores = cosine_similarity(drug_emb, disease_emb)

# Build output table
rows = []
for i, drug in enumerate(drugs):
    for j, disease in enumerate(diseases):
        rows.append([drug, disease, float(scores[i, j])])

df = pd.DataFrame(rows, columns=["drug", "disease", "score"])
df.to_csv("global_scores.csv", index=False)

print("DONE → Saved global_scores.csv (drug–disease similarity ranking)")
