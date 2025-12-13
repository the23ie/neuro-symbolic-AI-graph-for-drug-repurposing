import pandas as pd

moa_file = "data/raw/chembl_moa.tsv"
out_file = "data/layers/drug_targets_clean.csv"

print("Loading ChEMBL MoA...")
df = pd.read_csv(moa_file, sep="\t", dtype=str).fillna("")

# Keep only needed columns
df = df[["chembl_id", "uniprot_id", "protein_name"]]

# Rename to standard schema
df = df.rename(columns={
    "chembl_id": "drug_id",
    "uniprot_id": "gene_id",
    "protein_name": "action"
})

# Remove rows without a gene
df = df[df["gene_id"] != ""]

df.to_csv(out_file, index=False)
print(f"Saved {len(df)} drug-target pairs → {out_file}")
