# symbolic_module/rules.py
"""
Simple PoLo-style symbolic rules for Laptop 3.
Each rule returns 0/1 (or 0..1) and we combine them into a symbolic_score.
"""

import pandas as pd
from typing import List

def load_drug_properties(path="data/drug_properties.csv"):
    try:
        df = pd.read_csv(path)
        df = df.set_index("drug")
        return df
    except Exception:
        # return empty df with expected columns
        return pd.DataFrame(columns=["BBB","toxicity"])

def load_pathway_genes(path="data/pathway_genes.csv"):
    try:
        df = pd.read_csv(path)
        return set(df["gene"].astype(str).tolist())
    except Exception:
        return set()

def target_in_pathway(path: List[str], pathway_genes:set) -> int:
    """
    Return 1 if any node in the path is a pathway gene.
    """
    for n in path:
        if n in pathway_genes:
            return 1
    return 0

def bbb_check(drug:str, drug_props: pd.DataFrame) -> float:
    """
    Binary BBB check. If property missing, return 0. For heuristics later, you can use MW/PSA.
    """
    if drug not in drug_props.index:
        return 0.0
    val = str(drug_props.loc[drug].get("BBB", "")).upper()
    return 1.0 if val in ("YES","TRUE","1") else 0.0

def toxicity_ok(drug:str, drug_props: pd.DataFrame) -> float:
    """
    Return 1 if toxicity not high, 0 if HIGH or unknown -> 0.5 for MEDIUM (if provided).
    """
    if drug not in drug_props.index:
        return 0.0
    tox = str(drug_props.loc[drug].get("toxicity", "")).upper()
    if tox == "HIGH":
        return 0.0
    if tox == "MEDIUM":
        return 0.5
    if tox in ("LOW","NONE","0"):
        return 1.0
    # unknown -> conservative 0.5
    return 0.5

def mechanism_consistent(path: List[str]) -> float:
    """
    Placeholder: returns 1.0 by default.
    You can enhance to detect contradictions (e.g., drug activates protein known to worsen disease).
    """
    return 1.0

def meta_path_score(path: List[str]) -> float:
    """
    Prefer common templates like:
      Drug -> Target -> Pathway -> Disease
      Drug -> SimilarDrug -> Target -> Disease
    This function gives a small boost if path length and types match heuristics.
    For the prototype, we use path length heuristic: shorter and containing 'Pathway' nodes is better.
    """
    # Heuristic: shorter is better; presence of 'Pathway' node (substring) gives boost
    score = max(0.0, 1.0 - (len(path)-2)*0.15)
    for node in path:
        if "pathway" in node.lower() or "path" in node.lower():
            score += 0.2
            break
    return min(score, 1.0)
