import pandas as pd

in_file = "data/raw/human_genes_info"
out_file = "data/layers/genes.csv"

# NCBI format columns:
# tax_id, GeneID, Symbol, LocusTag, Synonyms, dbXrefs, chromosome, map_location,
# description, type_of_gene, ...

cols = [
    "tax_id", "GeneID", "Symbol", "Synonyms",
    "dbXrefs", "description", "type_of_gene"
]

df = pd.read_csv(
    in_file,
    sep="\t",
    names=cols,
    usecols=[0,1,2,4,5,8,9],
    dtype=str,
    comment="#"
)

# Keep only HOMO SAPIENS + protein coding
df = df[df["type_of_gene"] == "protein-coding"]

df = df[["GeneID", "Symbol", "description"]].fillna("")

df.to_csv(out_file, index=False)
print(f"Saved {len(df)} protein-coding genes → {out_file}")
