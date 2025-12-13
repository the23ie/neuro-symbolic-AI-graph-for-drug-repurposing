# symbolic_module/rules.py

import re

def rule_pathway_overlap(drug_pathways, disease_pathways):
    """Boost if drug and disease share pathways."""
    overlap = set(drug_pathways) & set(disease_pathways)
    score = len(overlap) * 0.2   # weight is learnable later
    explanation = f"Shared pathways: {', '.join(overlap)}" if overlap else "No shared pathways"
    return score, explanation


def rule_target_in_disease_genes(drug_targets, disease_genes):
    """Boost score if drug targets appear in disease gene list."""
    hits = set(drug_targets) & set(disease_genes)
    score = len(hits) * 0.3
    explanation = f"Drug hits disease genes: {', '.join(hits)}" if hits else "No direct target hits"
    return score, explanation


def rule_antagonistic_gene_interactions(drug_targets, opposite_genes):
    """Penalty: Drug targets may worsen the disease."""
    hits = set(drug_targets) & set(opposite_genes)
    score = -0.4 * len(hits)
    explanation = f"Antagonistic gene interactions: {', '.join(hits)}" if hits else "No harmful gene interactions"
    return score, explanation


def rule_bbb_requirement(drug_properties, disease):
    """Boost if drug crosses BBB for CNS diseases, penalize if not."""
    needs_bbb = disease.lower() in ["alzheimer's", "parkinson's", "epilepsy"]
    bbb_ok = drug_properties.get("bbb", False)

    if needs_bbb and not bbb_ok:
        return -0.5, "Disease requires BBB crossing but drug cannot cross"
    if needs_bbb and bbb_ok:
        return 0.3, "Drug crosses BBB"
    return 0.0, "BBB not relevant"


def rule_toxicity(drug_properties):
    """Penalty based on toxicity severity."""
    tox = drug_properties.get("toxicity", 0)
    score = -0.2 * tox
    explanation = f"Toxicity penalty: level {tox}"
    return score, explanation


def apply_all_rules(context):
    """
    Combine all PoLo-style rules.
    context = {
        'drug_targets': [...],
        'drug_pathways': [...],
        'drug_properties': {...},
        'disease': 'Alzheimers',
        'disease_genes': [...],
        'opposite_genes': [...],
    }
    """
    rules = [
        rule_pathway_overlap(
            context["drug_pathways"],
            context["disease_pathways"]
        ),
        rule_target_in_disease_genes(
            context["drug_targets"],
            context["disease_genes"]
        ),
        rule_antagonistic_gene_interactions(
            context["drug_targets"],
            context["opposite_genes"]
        ),
        rule_bbb_requirement(
            context["drug_properties"],
            context["disease"]
        ),
        rule_toxicity(
            context["drug_properties"]
        ),
    ]

    total_score = sum(r[0] for r in rules)
    explanations = [r[1] for r in rules]

    return total_score, explanations
