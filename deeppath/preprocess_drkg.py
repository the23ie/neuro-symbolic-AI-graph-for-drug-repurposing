import pickle
from collections import defaultdict

train_file = "data/drkg/train.txt"

entity2id = {}
relation2id = {}
adj_list = defaultdict(list)

def get_id(d, k):
    if k not in d:
        d[k] = len(d)
    return d[k]

with open(train_file) as f:
    for line in f:
        h, r, t = line.strip().split()
        hid = get_id(entity2id, h)
        rid = get_id(relation2id, r)
        tid = get_id(entity2id, t)
        adj_list[hid].append((rid, tid))

# save entity2id
with open("data/drkg/entity2id.txt", "w") as f:
    for k, v in entity2id.items():
        f.write("%s\t%d\n" % (k, v))

# save relation2id
with open("data/drkg/relation2id.txt", "w") as f:
    for k, v in relation2id.items():
        f.write("%s\t%d\n" % (k, v))

# save adjacency list
with open("data/drkg/adj_list.pkl", "wb") as f:
    pickle.dump(adj_list, f, protocol=2)

print("DONE")
print("Entities:", len(entity2id))
print("Relations:", len(relation2id))
print("Edges:", sum(len(v) for v in adj_list.values()))
