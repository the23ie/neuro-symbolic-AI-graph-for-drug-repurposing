import pandas as pd
from chembl_webresource_client.new_client import new_client

mechanisms = new_client.mechanism

print("Fetching ChEMBL Mechanisms of Action (MoA)... This may take a few minutes.")

# Fetch all mechanisms
data = mechanisms.filter(target_chembl_id__isnull=False).only(
    ['mec_id', 'molecule_chembl_id', 'target_chembl_id', 'action_type', 'target_components']
)

records = []

for row in data:
    drug = row.get('molecule_chembl_id')
    action = row.get('action_type', '').lower()

    # target_components contains UniProt IDs
    comps = row.get('target_components') or []

    for comp in comps:
        uniprot = comp.get('accession')
        if uniprot:
            records.append([drug, uniprot, action])

df = pd.DataFrame(records, columns=["drug_id", "gene_id", "action"])

# drop missing
df = df[df["drug_id"].notna() & df["gene_id"].notna()]

df.to_csv("data/layers/drug_targets_clean.csv", index=False)

print(f"Saved {len(df)} drug–target pairs → data/layers/drug_targets_clean.csv")
