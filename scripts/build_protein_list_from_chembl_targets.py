import pandas as pd

in_file = "data/raw/chembl_moa.tsv"
out_file = "data/layers/proteins.csv"

rows = []
with open(in_file, "r") as f:
    for line in f:
        if line.startswith("#"):
            continue
        parts = line.strip().split("\t")
        if len(parts) < 3:
            continue
        uniprot = parts[0]
        target_chembl = parts[1]
        name = parts[2]

        rows.append([uniprot, name, target_chembl])

df = pd.DataFrame(rows, columns=["uniprot_id", "protein_name", "target_chembl_id"])
df.to_csv(out_file, index=False)

print(f"Saved {len(df)} proteins → {out_file}")
