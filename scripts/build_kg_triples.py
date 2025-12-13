import os
import pandas as pd

def load_csv(path, required_cols):
    df = pd.read_csv(path, dtype=str).fillna("")
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in {path}: {missing}")
    return df

def main(in_dir, out_file):
    triples = []

    # 1) DRUG TARGETS
    drug_targets = load_csv(
        f"{in_dir}/layers/drug_targets.csv",
        ["drug_id", "gene_id", "action"]
    )
    for _, row in drug_targets.iterrows():
        triples.append([row["drug_id"], "targets", row["gene_id"]])

    # 2) GENE-GENE INTERACTIONS
    gg = load_csv(
        f"{in_dir}/layers/gene_interactions.csv",
        ["gene1", "gene2", "score"]
    )
    for _, row in gg.iterrows():
        triples.append([row["gene1"], "interacts_with", row["gene2"]])

    # 3) GENE → PATHWAY
    gp = load_csv(
        f"{in_dir}/layers/gene_pathway.csv",
        ["gene_id", "pathway_id"]
    )
    for _, row in gp.iterrows():
        triples.append([row["gene_id"], "in_pathway", row["pathway_id"]])

    # 4) DISEASE–GENE ASSOCIATIONS
    dg = load_csv(
        f"{in_dir}/layers/disease_gene.csv",
        ["gene_id", "disease_id", "score"]
    )
    for _, row in dg.iterrows():
        triples.append([row["gene_id"], "associated_with", row["disease_id"]])

    # OUTPUT
    triples_df = pd.DataFrame(triples, columns=["head", "relation", "tail"])
    triples_df.to_csv(out_file, index=False)

    print(f"Wrote {len(triples_df)} triples → {out_file}")

    nodes = sorted(set(list(triples_df["head"]) + list(triples_df["tail"])))
    pd.DataFrame({"node": nodes}).to_csv("data/node_lookup.csv", index=False)
    print(f"Node lookup written: {len(nodes)} nodes")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    main(args.in_dir, args.out)
