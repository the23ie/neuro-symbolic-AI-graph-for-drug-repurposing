import pandas as pd
from chembl_webresource_client.new_client import new_client
import mygene

mg = mygene.MyGeneInfo()

drugs = pd.read_csv("data/layers/drugs.csv", dtype=str)

drug_ids = drugs["drug_id"].unique()

records = []

target = new_client.target
activity = new_client.activity

for d in drug_ids:
    try:
        acts = activity.filter(molecule_chembl_id=d)
    except:
        continue

    for a in acts:
        if "target_chembl_id" not in a:
            continue

        tid = a["target_chembl_id"]
        t = target.filter(target_chembl_id=tid)

        if len(t) == 0:
            continue

        tgt = t[0]

        # Filter only single protein targets
        if tgt["target_type"] != "SINGLE PROTEIN":
            continue

        gene = tgt["pref_name"]

        records.append({
            "drug_id": d,
            "gene_name": gene,
            "action": "binds"
        })

df = pd.DataFrame(records).drop_duplicates()

# Map gene names → official gene symbols
mapped = mg.querymany(
    df["gene_name"].tolist(),
    scopes="name",
    fields="symbol",
    species="human",
    as_dataframe=True
)

df["gene_symbol"] = mapped["symbol"].tolist()
df = df.dropna(subset=["gene_symbol"])

df = df[["drug_id", "gene_symbol", "action"]]

df.to_csv("data/layers/drug_targets_clean.csv", index=False)
print("Saved clean drug targets → data/layers/drug_targets_clean.csv")
print(df.head())
