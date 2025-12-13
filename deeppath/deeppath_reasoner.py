"""
DeepPath-style multi-hop reasoning on DRKG
Python 3 compatible
"""

import os
import random
import pickle
from tqdm import tqdm

DATA_DIR = "data/drkg"
MAX_STEPS = 3
EPISODES = 200
OUTPUT_FILE = "deeppath_paths.txt"

print("Loading entity & relation maps...")

entity2id = {}
id2entity = {}

with open(os.path.join(DATA_DIR, "entity2id.txt")) as f:
    for line in f:
        k, v = line.strip().split()
        entity2id[k] = int(v)
        id2entity[int(v)] = k

relation2id = {}
id2relation = {}

with open(os.path.join(DATA_DIR, "relation2id.txt")) as f:
    for line in f:
        k, v = line.strip().split()
        relation2id[k] = int(v)
        id2relation[int(v)] = k

print("Loading adjacency list...")
with open(os.path.join(DATA_DIR, "adj_list.pkl"), "rb") as f:
    adj_list = pickle.load(f)

print("Loading compound & disease IDs...")
with open(os.path.join(DATA_DIR, "compound_ids.pkl"), "rb") as f:
    compound_nodes = pickle.load(f)

with open(os.path.join(DATA_DIR, "disease_ids.pkl"), "rb") as f:
    disease_nodes = set(pickle.load(f))

print("Compounds:", len(compound_nodes))
print("Diseases:", len(disease_nodes))

if not compound_nodes or not disease_nodes:
    raise RuntimeError("Compound or Disease lists are EMPTY — check preprocessing!")

def random_walk(start, max_steps=3):
    path = [start]
    current = start

    for _ in range(max_steps):
        if current not in adj_list:
            break
        edges = adj_list[current]
        if not edges:
            break
        rel, nxt = random.choice(edges)
        path.append((rel, nxt))
        current = nxt
        if current in disease_nodes:
            return path
    return None

print("Starting DeepPath-style reasoning...")
paths_found = []

for _ in tqdm(range(EPISODES)):
    start = random.choice(compound_nodes)
    result = random_walk(start, MAX_STEPS)
    if result:
        paths_found.append(result)

print("Saving paths...")
with open(OUTPUT_FILE, "w") as f:
    for path in paths_found:
        out = [id2entity[path[0]]]
        for rel, ent in path[1:]:
            out.append(id2relation[rel])
            out.append(id2entity[ent])
        f.write(" -> ".join(out) + "\n")

print("DONE")
print("Total paths found:", len(paths_found))
print("Saved to:", OUTPUT_FILE)
