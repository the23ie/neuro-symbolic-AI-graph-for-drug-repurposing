import numpy as np
import pandas as pd
import json
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
import os

# Load embeddings
entity_emb = np.load("data/drkg/embed/DRKG_TransE_l2_entity.npy")

# Load entity list
entities = []
with open("data/drkg/embed/entities.tsv") as f:
    for line in f:
        entities.append(line.strip())

# Separate drugs and diseases
drug_ids = [i for i,e in enumerate(entities) if e.startswith("Compound::")]
disease_ids = [i for i,e in enumerate(entities) if e.startswith("Disease::")]

print(f"Found {len(drug_ids)} drugs, {len(disease_ids)} diseases")

drug_emb = entity_emb[drug_ids]
disease_emb = entity_emb[disease_ids]

BLOCK = 1000
OUT = "data/global_scores.csv"

write_header = not os.path.exists(OUT)

with open(OUT, "a") as fout:
    if write_header:
        fout.write("drug,disease,score\n")

    for i in tqdm(range(0, len(drug_emb), BLOCK), desc="Computing blocks"):
        d_block = drug_emb[i:i+BLOCK]
        scores = cosine_similarity(d_block, disease_emb)

        for di in range(scores.shape[0]):
            drug_name = entities[drug_ids[i + di]]
            for dj in range(scores.shape[1]):
                disease_name = entities[disease_ids[dj]]
                fout.write(f"{drug_name},{disease_name},{scores[di, dj]:.6f}\n")

        fout.flush()
