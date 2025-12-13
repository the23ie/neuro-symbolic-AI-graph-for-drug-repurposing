import pandas as pd

input_file = "data/raw/Ensembl2Reactome.txt"
output_file = "data/layers/genes.csv"

print("Reading Reactome → Ensembl mapping...")

df = pd.read_csv(input_file, sep="\t", header=None,
                 names=["ensembl_id", "reactome_id", "species", "pathway_name", "url"])

# Only keep Human genes
df = df[df["species"] == "Homo sapiens"]

# Extract unique Ensembl IDs
genes = df[["ensembl_id"]].drop_duplicates()

# Add a placeholder gene symbol (OPTIONAL)
genes["gene_symbol"] = genes["ensembl_id"]

# Reorder
genes = genes[["gene_symbol", "ensembl_id"]]

genes.to_csv(output_file, index=False)

print(f"Saved {len(genes)} human genes → {output_file}")
