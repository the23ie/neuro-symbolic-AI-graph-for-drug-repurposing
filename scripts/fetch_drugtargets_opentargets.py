#!/usr/bin/env python3
"""
Fetch drug -> targets via ChEMBL and fetch disease->gene via Open Targets.
Writes:
 - data/layers/drug_targets.csv  (drug_id, gene_symbol, evidence)
 - data/layers/diseases.csv     (disease_id, disease_name)
 - data/layers/disease_gene.csv (disease_id, gene_symbol, score)
Requirements: chembl_webresource_client, mygene, requests, pandas, tqdm
"""
import time, sys, re, json
from pathlib import Path
import pandas as pd
from tqdm import tqdm
import requests
import mygene

# chembl client
try:
    from chembl_webresource_client.new_client import new_client
except Exception as e:
    print("chembl_webresource_client not available:", e, file=sys.stderr)
    new_client = None

ROOT = Path.cwd()
LAYERS = ROOT / "data" / "layers"
RAW = ROOT / "data" / "raw"
LAYERS.mkdir(parents=True, exist_ok=True)

# Load drugs
drugs_path = LAYERS / "drugs.csv"
if not drugs_path.exists():
    raise FileNotFoundError(drugs_path)
drugs = pd.read_csv(drugs_path, dtype=str).fillna("")

# 1) Build STRING ID -> gene symbol mapping from alias file if available
alias_candidates = list(RAW.glob("9606.protein.aliases*.txt.gz"))
string_to_symbol = {}
if alias_candidates:
    import gzip
    alias_file = alias_candidates[0]
    print("Parsing STRING alias file:", alias_file)
    # alias file columns vary; typical format: string_protein_id <tab> alias <tab> alias_type
    with gzip.open(alias_file, "rt", errors="ignore") as fh:
        for line in fh:
            parts = line.strip().split("\t")
            if len(parts) < 2:
                continue
            sid = parts[0]
            alias = parts[1]
            # heuristics: prefer aliases that look like gene symbols (mostly uppercase, len<10)
            if re.fullmatch(r"[A-Z0-9\-]{2,10}", alias):
                # prefer the first good alias we see
                if sid not in string_to_symbol:
                    string_to_symbol[sid] = alias
    print("Mapped STRING ids -> gene symbols (sample):", list(string_to_symbol.items())[:5])
else:
    print("No STRING alias file found; continuing without direct mapping.")

# 2) Load existing genes.csv (these are currently STRING ids)
genes_csv = LAYERS / "genes.csv"
if not genes_csv.exists():
    print("genes.csv missing; can't map genes. Exiting.")
    sys.exit(1)
genes_df = pd.read_csv(genes_csv, dtype=str).fillna("")
# create gene_symbol list by mapping string ids where possible; fallback to original id
def map_string_to_symbol(sid):
    if sid in string_to_symbol:
        return string_to_symbol[sid]
    # fallback heuristics: if sid looks like ENSG or numeric, return as-is
    return sid

genes_df['gene_symbol'] = genes_df['gene_id'].apply(map_string_to_symbol)
# write a mapped genes file for inspection
genes_df[['gene_id','gene_symbol']].to_csv(LAYERS/"genes_mapped.csv", index=False)

# 3) Resolve drug -> targets from ChEMBL (best-effort)
drug_targets = []
if new_client is None:
    print("ChEMBL client not available; skipping drug->target extraction.")
else:
    molecule = new_client.molecule
    activity = new_client.activity
    # iterate drugs; prefer direct DrugBank -> ChEMBL mapping via molecule_properties.drugbank
    for _, r in drugs.iterrows():
        dbid = str(r['drug_id']).strip()
        name = str(r['drug_name']).strip()
        chembl_id = None
        # attempt search by drugbank crossref
        try:
            q = molecule.filter(molecule_properties__drugbank__exact=dbid)
            results = list(q)[:1]
            if results:
                chembl_id = results[0].get('molecule_chembl_id')
        except Exception:
            pass
        # fallback: search by pref_name
        if not chembl_id:
            try:
                q2 = molecule.filter(pref_name__icontains=name)
                results2 = list(q2)[:2]
                if results2:
                    chembl_id = results2[0].get('molecule_chembl_id')
            except Exception:
                pass
        # if we have a chembl_id, fetch activities (which include target info)
        if chembl_id:
            try:
                acts = activity.filter(molecule_chembl_id=chembl_id).only(['target_pref_name','target_chembl_id','target_organism'])[:500]
                for a in acts:
                    tname = a.get('target_pref_name') or a.get('target_chembl_id')
                    # keep only human targets
                    org = a.get('target_organism') or ''
                    if 'Homo sapiens' in org or org=='' or 'human' in org.lower():
                        drug_targets.append((dbid, tname, "chembl_activity"))
            except Exception:
                pass
        # If none found, try searching activities by drug name
        if not chembl_id:
            try:
                acts2 = activity.filter(pmid__isnull=False).filter(description__icontains=name)[:100]
                for a in acts2:
                    tname = a.get('target_pref_name') or a.get('target_chembl_id')
                    drug_targets.append((dbid, tname, "chembl_textsearch"))
            except Exception:
                pass

# dedupe & save
if drug_targets:
    dt_df = pd.DataFrame(drug_targets, columns=['drug_id','gene_symbol','evidence'])
    dt_df = dt_df.drop_duplicates().reset_index(drop=True)
    dt_df.to_csv(LAYERS/"drug_targets.csv", index=False)
    print("WROTE drug_targets.csv rows:", len(dt_df))
else:
    print("No drug-target pairs found via ChEMBL for provided drugs; you may need manual curation.")

# 4) Map gene_symbol -> Ensembl gene id using MyGene.info (for Open Targets)
mg = mygene.MyGeneInfo()
unique_symbols = genes_df['gene_symbol'].unique().tolist()
print("Mapping", len(unique_symbols), "gene symbols to Ensembl IDs (batched)...")
symbol_to_ensembl = {}
batch_size = 500
for i in range(0, len(unique_symbols), batch_size):
    batch = unique_symbols[i:i+batch_size]
    try:
        res = mg.querymany(batch, scopes='symbol', fields='ensembl.gene', species='human', as_dataframe=False)
        for r in res:
            query = r.get('query')
            if 'notfound' in r and r['notfound']:
                continue
            ensembl = None
            if 'ensembl' in r:
                e = r['ensembl']
                # ensembl can be dict or list
                if isinstance(e, list):
                    ensembl = e[0].get('gene')
                elif isinstance(e, dict):
                    ensembl = e.get('gene')
            if ensembl:
                symbol_to_ensembl[query] = ensembl
    except Exception as e:
        print("MyGene batch failed:", e)
    time.sleep(0.5)

print("Mapped symbols -> ensembl sample:", list(symbol_to_ensembl.items())[:5])

# 5) Query Open Targets for disease associations per Ensembl gene
# We'll use the Open Targets public REST filter endpoint: /public/association/filter?target=ENSG...
OT_BASE = "https://platform.opentargets.org/api/v4/graphql"
# GraphQL query to get top disease associations for a gene (by ensembl id)
gql_template = '''
query getAssociations($ensg:String!, $size:Int!) {
  target(ensemblId: $ensg) {
    id
    approvedSymbol
    associations(diseaseType: DISEASE, size: $size) {
      count
      rows {
        disease {
          id
          name
        }
        score
      }
    }
  }
}
'''
# Prepare outputs
disease_rows = []  # disease_id, disease_name
disease_gene = []  # disease_id, gene_symbol, score

ensembl_items = list(symbol_to_ensembl.items())
print("Querying Open Targets for", len(ensembl_items), "genes (this may take some minutes)...")
for gene_symbol, ensg in tqdm(ensembl_items):
    # GraphQL payload
    payload = {"query": gql_template, "variables": {"ensg": ensg, "size": 50}}
    try:
        r = requests.post(OT_BASE, json=payload, timeout=60)
        if r.status_code != 200:
            # skip on error
            # print("OT API error", r.status_code, r.text)
            time.sleep(0.2)
            continue
        data = r.json().get('data') or {}
        if not data.get('target'):
            time.sleep(0.1)
            continue
        assoc_info = data['target'].get('associations') or {}
        rows = assoc_info.get('rows') or []
        for row in rows:
            d = row['disease']
            did = d['id']
            dname = d['name']
            score = row.get('score') or 0.0
            disease_rows.append((did, dname))
            disease_gene.append((did, gene_symbol, float(score)))
    except Exception as e:
        # skip on exceptions
        # print("Query error for", ensg, e)
        time.sleep(0.2)
    time.sleep(0.1)  # polite

# dedupe and write diseases.csv and disease_gene.csv
if disease_rows:
    dd = pd.DataFrame(disease_rows, columns=['disease_id','disease_name']).drop_duplicates().reset_index(drop=True)
    dd.to_csv(LAYERS/"diseases.csv", index=False)
    dg = pd.DataFrame(disease_gene, columns=['disease_id','gene_symbol','score']).drop_duplicates().reset_index(drop=True)
    dg.to_csv(LAYERS/"disease_gene.csv", index=False)
    print("WROTE diseases.csv (rows):", len(dd), "and disease_gene.csv (rows):", len(dg))
else:
    print("No disease associations retrieved from Open Targets (check mapping or API availability).")

print("Finished. Check data/layers for drug_targets.csv, diseases.csv, disease_gene.csv.")
