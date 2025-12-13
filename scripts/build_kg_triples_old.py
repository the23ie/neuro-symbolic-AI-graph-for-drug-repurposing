#!/usr/bin/env python3
"""
scripts/build_kg_triples.py

Usage:
  python scripts/build_kg_triples.py --in_dir data --out data/kg_triples.csv

Input expected (CSV files inside data/):
 - drugs.csv (id,name,alt_ids,smiles,source)
 - proteins.csv (id,symbol,uniprot,description)
 - pathways.csv (id,name,source)
 - diseases.csv (id,name,doid)
 - phenotypes.csv (id,name,hpo)
 - relations CSVs (optional): e.g. drug_protein_edges.csv, pathway_disease_edges.csv, etc.

If per-relation CSVs are absent, the script will try to infer simple edges from basic fields.
"""

import argparse
import os
import csv
import pandas as pd
from pathlib import Path
from typing import List, Tuple

NODE_PREFIXES = {
    "drugs.csv": "Drug",
    "proteins.csv": "Protein",
    "pathways.csv": "Pathway",
    "diseases.csv": "Disease",
    "phenotypes.csv": "Phenotype",
}

DEFAULT_RELATIONS = [
    ("drugs.csv", "proteins.csv", "binds", "drug_protein_edges.csv"),
    ("drugs.csv", "proteins.csv", "inhibits", "drug_protein_inhibits.csv"),
    ("drugs.csv", "proteins.csv", "activates", "drug_protein_activates.csv"),
    ("proteins.csv", "pathways.csv", "part_of", "protein_pathway_edges.csv"),
    ("pathways.csv", "diseases.csv", "associated_with", "pathway_disease_edges.csv"),
    ("proteins.csv", "diseases.csv", "associated_with", "protein_disease_edges.csv"),
    ("drugs.csv", "diseases.csv", "treats", "drug_disease_edges.csv"),
    ("drugs.csv", "phenotypes.csv", "has_side_effect", "drug_sideeffect_edges.csv"),
    ("diseases.csv", "phenotypes.csv", "has_phenotype", "disease_phenotype_edges.csv"),
]

def load_nodes(in_dir: Path):
    nodes = {}
    for fname, prefix in NODE_PREFIXES.items():
        path = in_dir / fname
        if not path.exists():
            continue
        df = pd.read_csv(path, dtype=str).fillna("")
        # ensure id and name exist
        if "id" not in df.columns and "name" in df.columns:
            df["id"] = df["name"].str.replace(r"\s+", "_", regex=True).str.lower()
        for _, row in df.iterrows():
            nid = str(row.get("id")).strip()
            name = str(row.get("name", "")).strip()
            if not nid:
                continue
            key = f"{prefix}:{nid}"
            nodes[key] = {
                "prefix": prefix,
                "id": nid,
                "name": name if name else nid,
                "meta": row.to_dict()
            }
    return nodes

def write_node_lookup(nodes: dict, out_path: Path):
    rows = []
    for k,v in nodes.items():
        rows.append({
            "node_key": k,
            "prefix": v["prefix"],
            "id": v["id"],
            "name": v["name"],
            "meta": str(v["meta"])
        })
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)

def normalize_label(s: str) -> str:
    if pd.isna(s):
        return ""
    s = str(s).strip()
    s = s.replace(" ", "_")
    s = s.replace("/", "_")
    return s

def read_relation_file(path: Path, src_prefix: str, tgt_prefix: str, rel_label: str) -> List[Tuple[str,str,str]]:
    rows = []
    if not path.exists():
        return rows
    df = pd.read_csv(path, dtype=str).fillna("")
    # expect columns head, tail or id_head/id_tail or drug/protein columns
    possible_head_cols = [c for c in df.columns if c.lower() in ("head","source","drug","drug_id","drug_name","id_head")]
    possible_tail_cols = [c for c in df.columns if c.lower() in ("tail","target","protein","protein_id","protein_name","id_tail","disease","disease_id")]
    if not possible_head_cols or not possible_tail_cols:
        # fallback: use first two columns
        if len(df.columns) >= 2:
            hcol, tcol = df.columns[0], df.columns[1]
        else:
            return rows
    else:
        hcol, tcol = possible_head_cols[0], possible_tail_cols[0]
    for _, r in df.iterrows():
        head = normalize_label(str(r.get(hcol,"")))
        tail = normalize_label(str(r.get(tcol,"")))
        if head and tail:
            rows.append((f"{src_prefix}:{head}", rel_label, f"{tgt_prefix}:{tail}"))
    return rows

def infer_simple_edges(nodes: dict, in_dir: Path):
    # tries to find edges from basic columns in node files, e.g., drugs.csv may have target_protein column.
    edges = []
    # example: look for 'target' or 'target_uniprot' in drugs.csv
    drugs_path = in_dir / "drugs.csv"
    if drugs_path.exists():
        df = pd.read_csv(drugs_path, dtype=str).fillna("")
        for _, r in df.iterrows():
            drug_id = normalize_label(str(r.get("id", r.get("name", ""))))
            # look for target/protein columns
            for col in df.columns:
                if col.lower().startswith("target") or "protein" in col.lower():
                    vals = str(r.get(col,"")).split("|")
                    for v in vals:
                        v = normalize_label(v)
                        if v:
                            edges.append((f"Drug:{drug_id}", "binds", f"Protein:{v}"))
    return edges

def main(in_dir: str, out_file: str):
    in_dir = Path(in_dir)
    out_file = Path(out_file)
    nodes = load_nodes(in_dir)
    write_node_lookup(nodes, in_dir / "node_lookup.csv")
    # collect edges
    edges = []
    # read explicit relation files if present, else try defaults and inference
    for src_file, tgt_file, rel_label, rel_fname in DEFAULT_RELATIONS:
        src_prefix = NODE_PREFIXES.get(src_file, src_file.split(".")[0].capitalize())
        tgt_prefix = NODE_PREFIXES.get(tgt_file, tgt_file.split(".")[0].capitalize())
        rel_path = in_dir / rel_fname
        if rel_path.exists():
            rlist = read_relation_file(rel_path, src_prefix, tgt_prefix, rel_label)
            edges.extend(rlist)
        else:
            # try to infer or skip
            continue

    # also attempt to infer from node files
    edges.extend(infer_simple_edges(nodes, in_dir))

    # deduplicate and ensure nodes exist; if a node doesn't exist, still keep but keep plain key
    seen = set()
    out_rows = []
    for h, r, t in edges:
        key = (h, r, t)
        if key in seen:
            continue
        seen.add(key)
        out_rows.append({"head": h, "relation": r, "tail": t})

    # write CSV
    df_out = pd.DataFrame(out_rows)
    df_out.to_csv(out_file, index=False)
    print(f"WROTE {len(df_out)} triples to {out_file}")
    print(f"NODE LOOKUP written to {in_dir / 'node_lookup.csv'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_dir", default="data")
    parser.add_argument("--out", default="data/kg_triples.csv")
    args = parser.parse_args()
    main(args.in_dir, args.out)
