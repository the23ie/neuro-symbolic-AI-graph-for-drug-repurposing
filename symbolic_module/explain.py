# symbolic_module/explain.py
"""
Simple explanation generator for a selected best path.
"""

from typing import List

def generate_explanation(drug: str, path: List[str], symbolic_breakdown: dict) -> str:
    """
    Produce a readable mechanistic sentence from the best path and symbolic rule results.
    """
    if not path or len(path) < 2:
        return f"{drug}: no supporting path available."

    # Build short textual path (skip long nodes)
    path_str = " → ".join(path)
    passed = [k for k,v in symbolic_breakdown.items() if v]
    failed = [k for k,v in symbolic_breakdown.items() if not v]

    expl = (
        f"Candidate: {drug}\n"
        f"Best path: {path_str}\n"
        f"Symbolic rules passed: {', '.join(passed) if passed else 'None'}.\n"
        f"Rules failed: {', '.join(failed) if failed else 'None'}.\n"
        f"Short rationale: The path suggests a mechanistic chain linking the drug to the disease (see path)."
    )
    return expl
