# symbolic_module/aggregate_scores.py
"""
Aggregate neural + path + symbolic scores into final_ranked_candidates.csv

Usage:
python -m symbolic_module.aggregate_scores \
  --neural artifacts/global_scores.csv \
  --paths artifacts/paths.jsonl \
  --drugprops data/drug_properties.csv \
  --pathway data/pathway_genes.csv \
  --out artifacts/final_ranked_candidates.csv
"""

import argparse
import pandas as pd
import numpy as np
import json
import jsonlines
import sys
from symbolic_module import rules, explain

def compute_symbolic_score(drug, best_path, drug_props_df, pathway_genes):
    # apply rules and normalize to 0..1
    r1 = rules.target_in_pathway(best_path, pathway_genes)   # 0/1
    r2 = rules.bbb_check(drug, drug_props_df)               # 0..1
    r3 = rules.toxicity_ok(drug, drug_props_df)             # 0..1
    r4 = rules.mechanism_consistent(best_path)              # 0..1
    r5 = rules.meta_path_score(best_path)                   # 0..1
    raw = np.array([r1, r2, r3, r4, r5], dtype=float)
    # weighted sum (simple equal weights)
    symbolic_score = float(raw.mean())
    breakdown = {
        "target_in_pathway": float(r1),
        "bbb_check": float(r2),
        "toxicity_ok": float(r3),
        "mechanism_consistent": float(r4),
        "meta_path_score": float(r5)
    }
    return symbolic_score, breakdown

def read_paths_jsonl_safe(paths_jsonl):
    """
    Generator: yields valid dict items from a JSONL file.
    Skips blank/invalid lines and logs them to stderr.
    """
    try:
        with open(paths_jsonl, "r", encoding="utf-8") as fh:
            for i, raw in enumerate(fh, start=1):
                line = raw.strip()
                if not line:
                    # skip blank lines silently
                    continue
                try:
                    obj = json.loads(line)
                    yield obj
                except Exception as e_json:
                    # try jsonlines reader fallback (handles some nonstandard cases)
                    try:
                        # attempt with jsonlines library read for the single line
                        # (this rarely fixes issues; kept as extra attempt)
                        obj = jsonlines.loads(line)  # type: ignore[attr-defined]
                        yield obj
                    except Exception:
                        print(f"[WARN] Skipping invalid JSON at line {i} in {paths_jsonl}: {e_json}", file=sys.stderr)
                        # optionally could print the line content truncated
                        continue
    except FileNotFoundError:
        print(f"[WARN] paths file not found: {paths_jsonl}. No paths will be processed.", file=sys.stderr)
        return

def aggregate(neural_csv, paths_jsonl, drugprops_csv, pathway_csv, out_csv,
              alpha=0.4, beta=0.35, gamma=0.25):
    # load neural scores
    try:
        neural_df = pd.read_csv(neural_csv)
    except Exception:
        print(f"[WARN] Could not read neural CSV: {neural_csv}. Proceeding with empty neural scores.", file=sys.stderr)
        neural_df = pd.DataFrame(columns=["drug","disease","score"])

    # load drug props and pathway genes
    drug_props_df = rules.load_drug_properties(drugprops_csv)
    pathway_genes = rules.load_pathway_genes(pathway_csv)

    results = []
    seen = set()

    # iterate safely over JSONL lines
    count_lines = 0
    count_valid = 0
    for item in read_paths_jsonl_safe(paths_jsonl):
        count_lines += 1
        if not isinstance(item, dict):
            continue
        count_valid += 1
        drug = item.get("drug")
        disease = item.get("disease")
        paths = item.get("paths", [])
        path_scores = item.get("path_scores", [])

        if not drug or not disease:
            print(f"[WARN] Skipping entry with missing drug/disease at JSONL item #{count_lines}", file=sys.stderr)
            continue

        # pick best path (by path_scores) if available, else blank
        if path_scores and len(path_scores)==len(paths):
            try:
                best_idx = int(np.argmax(path_scores))
            except Exception:
                best_idx = 0
            best_path = paths[best_idx]
            best_path_score = float(path_scores[best_idx])
        elif paths:
            best_path = paths[0]
            best_path_score = 0.0
        else:
            best_path = []
            best_path_score = 0.0

        # find neural score (if present)
        df_match = neural_df[(neural_df["drug"]==drug) & (neural_df["disease"]==disease)]
        if not df_match.empty:
            try:
                neural_score = float(df_match["score"].iloc[0])
            except Exception:
                neural_score = 0.0
        else:
            neural_score = 0.0

        symbolic_score, breakdown = compute_symbolic_score(drug, best_path, drug_props_df, pathway_genes)

        final_score = alpha * neural_score + beta * best_path_score + gamma * symbolic_score

        results.append({
            "drug": drug,
            "disease": disease,
            "final_score": final_score,
            "neural_score": neural_score,
            "best_path_score": best_path_score,
            "symbolic_score": symbolic_score,
            "best_path": " | ".join(best_path),
            "rule_target_in_pathway": breakdown["target_in_pathway"],
            "rule_bbb_check": breakdown["bbb_check"],
            "rule_toxicity_ok": breakdown["toxicity_ok"],
            "rule_mechanism_consistent": breakdown["mechanism_consistent"],
            "rule_meta_path_score": breakdown["meta_path_score"]
        })
        seen.add((drug,disease))

    # If some (drug,disease) pairs exist in neural_df but not in paths_jsonl, include them with empty path
    for _, row in neural_df.iterrows():
        drug = row["drug"]
        disease = row["disease"]
        key = (drug,disease)
        if key in seen:
            continue
        try:
            neural_score = float(row["score"])
        except Exception:
            neural_score = 0.0
        best_path = []
        best_path_score = 0.0
        symbolic_score, breakdown = compute_symbolic_score(drug, best_path, drug_props_df, pathway_genes)
        final_score = alpha * neural_score + beta * best_path_score + gamma * symbolic_score
        results.append({
            "drug": drug,
            "disease": disease,
            "final_score": final_score,
            "neural_score": neural_score,
            "best_path_score": best_path_score,
            "symbolic_score": symbolic_score,
            "best_path": "",
            "rule_target_in_pathway": breakdown["target_in_pathway"],
            "rule_bbb_check": breakdown["bbb_check"],
            "rule_toxicity_ok": breakdown["toxicity_ok"],
            "rule_mechanism_consistent": breakdown["mechanism_consistent"],
            "rule_meta_path_score": breakdown["meta_path_score"]
        })

    out_df = pd.DataFrame(results)
    out_df = out_df.sort_values("final_score", ascending=False).reset_index(drop=True)
    out_df.to_csv(out_csv, index=False)
    print(f"Wrote {len(out_df)} final candidates to {out_csv} (processed {count_lines} JSONL lines, {count_valid} valid).")
    return out_df

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--neural", default="artifacts/global_scores.csv")
    p.add_argument("--paths", default="artifacts/paths.jsonl")
    p.add_argument("--drugprops", default="data/drug_properties.csv")
    p.add_argument("--pathway", default="data/pathway_genes.csv")
    p.add_argument("--out", default="artifacts/final_ranked_candidates.csv")
    p.add_argument("--alpha", type=float, default=0.4)
    p.add_argument("--beta", type=float, default=0.35)
    p.add_argument("--gamma", type=float, default=0.25)
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    aggregate(args.neural, args.paths, args.drugprops, args.pathway, args.out, args.alpha, args.beta, args.gamma)
