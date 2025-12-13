import pandas as pd
import mygene

mg = mygene.MyGeneInfo()

df = pd.read_csv("data/layers/drug_targets.csv", dtype=str).fillna("")

# Query mygene: convert full gene names → official symbols
results = mg.querymany(
    df["gene_symbol"].tolist(),
    scopes="name,alias",
    fields="symbol",
    species="human",
    as_dataframe=True
)

# Merge results
mapped = df.join(results["symbol"], how="left")
mapped = mapped.rename(columns={"symbol": "gene_symbol_clean"})

mapped.to_csv("data/layers/drug_targets_normalized.csv", index=False)
print("Saved → data/layers/drug_targets_normalized.csv")
print(mapped.head())
