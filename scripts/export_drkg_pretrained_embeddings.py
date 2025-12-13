import numpy as np
import pandas as pd
import json

# Load DRKG entity list
entities = pd.read_csv("data/drkg/entities.txt", header=None)[0].tolist()
entity2id = {e: i for i, e in enumerate(entities)}

# Load pretrained embeddings
emb = np.load("data/drkg/embed/DRKG_TransE_l2_entity.npy")

# Save in your project format
np.save("embeddings.npy", emb)
with open("entity2id.json", "w") as f:
    json.dump(entity2id, f)

print("Saved:")
print(" - embeddings.npy")
print(" - entity2id.json")
