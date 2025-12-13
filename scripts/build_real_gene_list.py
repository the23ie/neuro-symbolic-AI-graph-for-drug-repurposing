import mygene
import pandas as pd

mg = mygene.MyGeneInfo()

print("Fetching human protein-coding gene list (~20,000 genes)...")

# Correct MyGene API query
res = mg.query(
    "type_of_gene:protein-coding",
    species="human",
    fields="symbol,ensembl.gene",
    size=20000
)

records = []
for r in res:
    symbol = r.get("symbol")
    if not symbol:
        continue

    ensembl = r.get("ensembl")
    if isinstance(ensembl, dict):
        ens_id = ensembl.get("gene")
    elif isinstance(ensembl, list) and len(ensembl) > 0:
        ens_id = ensembl[0].get("gene")
    else:
        continue

    if ens_id:
        records.append({
            "gene_symbol": symbol,
            "ensembl_id": ens_id
        })

df = pd.DataFrame(records).drop_duplicates()

df.to_csv("data/layers/genes.csv", index=False)

print(f"Saved {len(df)} genes → data/layers/genes.csv")
