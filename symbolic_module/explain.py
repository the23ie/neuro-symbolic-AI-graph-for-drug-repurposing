# symbolic_module/explain.py

def format_explanation(drug, disease, neural_score, symbolic_score, rules_explanations, best_path):
    text = []
    text.append(f"Drug: {drug}")
    text.append(f"Disease: {disease}")
    text.append("")
    text.append(f"Neural Score: {neural_score:.3f}")
    text.append(f"Symbolic Score: {symbolic_score:.3f}")
    text.append("")
    text.append("Best Biological Path:")
    text.append(f"  {best_path}")
    text.append("")
    text.append("Symbolic Reasoning Breakdown:")
    for exp in rules_explanations:
        text.append(f"  - {exp}")
    return "\n".join(text)
