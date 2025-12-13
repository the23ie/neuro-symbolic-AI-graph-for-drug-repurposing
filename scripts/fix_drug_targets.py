import pandas as pd

drug_file = "data/layers/drug_targets.csv"
genes_map_file = "data/layers/genes_mapped.csv"
out_file = "data/layers/drug_targets_clean.csv"

# Load raw drug-target data
df = pd.read_csv(drug_file, dtype=str).fillna("")

# Load gene mapping: gene_symbol -> gene_id (STRING-based id)
genes = pd.read_csv(genes_map_file, dtype=str).fillna("")

# Create lookup dictionary
symbol_to_geneid = dict(zip(genes["gene_symbol"], genes["gene_id"]))

# Map symbols to gene_id
df["gene_id"] = df["gene_symbol"].map(symbol_to_geneid)

# Drop rows where mapping failed
df = df[df["gene_id"].notna()]

# Add "action" column (placeholder = unknown)
df["action"] = "binds"

# Keep only required columns
df = df[["drug_id", "gene_id", "action"]]

df.to_csv(out_file, index=False)
print(f"Saved cleaned targets → {out_file}")
print(df.head())
