import pandas as pd
import gzip
import os

INPUT = "data/raw/CTD_curated_genes_diseases.tsv.gz"
OUT_DISEASE = "data/layers/diseases.csv"
OUT_GDA = "data/layers/disease_gene.csv"

print("Reading CTD curated dataset:", INPUT)

rows = []
disease_rows = set()

with gzip.open(INPUT, "rt", encoding="utf-8") as f:
    for line in f:
        if line.startswith("#"):
            continue
        
        parts = line.strip().split("\t")
        if len(parts) < 4:
            continue
        
        gene_symbol = parts[0]
        gene_id = parts[1]
        disease_name = parts[2]
        disease_id = parts[3]
        
        disease_rows.add((disease_id, disease_name))
        
        rows.append((gene_symbol, disease_id, 1))  # score=1

print("Building DataFrames...")

diseases_df = pd.DataFrame(list(disease_rows), columns=["disease_id", "disease_name"])
diseases_df.to_csv(OUT_DISEASE, index=False)

gda_df = pd.DataFrame(rows, columns=["gene_id", "disease_id", "score"])
gda_df.to_csv(OUT_GDA, index=False)

print("DONE.")
print("Diseases:", len(diseases_df))
print("Gene–Disease associations:", len(gda_df))
print("Saved to:")
print(" →", OUT_DISEASE)
print(" →", OUT_GDA)
