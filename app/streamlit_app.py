# app/streamlit_app.py
"""
Streamlit UI for Laptop 3 — Neuro-Symbolic Drug Repurposing
Updated: uses Graphviz for path visualization (reliable on macOS) instead of pyvis.
"""

import os
import streamlit as st
import pandas as pd
import graphviz
from typing import List

st.set_page_config(page_title="Neuro-Symbolic Drug Repurposing", layout="wide")

DATA_CSV = "artifacts/final_ranked_candidates.csv"

st.title("Neuro-Symbolic Drug Repurposing — Laptop 3 Demo")

if not os.path.exists(DATA_CSV):
    st.warning(f"Missing {DATA_CSV}. Run the aggregator first:\n\n"
               "`python -m symbolic_module.aggregate_scores --neural artifacts/global_scores.csv "
               "--paths artifacts/paths.jsonl --drugprops data/drug_properties.csv "
               "--pathway data/pathway_genes.csv --out artifacts/final_ranked_candidates.csv`")
    st.stop()

# Load data
try:
    df = pd.read_csv(DATA_CSV)
except Exception as e:
    st.error(f"Failed to read {DATA_CSV}: {e}")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")
top_k = st.sidebar.number_input("Top K to show", min_value=1, max_value=500, value=20)
min_score = st.sidebar.slider("Min final score", 0.0, 1.0, 0.0, 0.01)

filtered = df[df["final_score"] >= min_score].copy()
filtered = filtered.sort_values("final_score", ascending=False).head(top_k)

st.subheader("Top Candidates")
st.dataframe(filtered[["drug", "disease", "final_score", "neural_score", "best_path_score", "symbolic_score"]].reset_index(drop=True))

# Candidate selection
candidates = filtered["drug"].tolist()
if not candidates:
    st.info("No candidates match the current filter.")
    st.stop()

sel = st.selectbox("Select a candidate to inspect", candidates)

if sel:
    row = df[df["drug"] == sel].iloc[0]

    st.markdown("### Candidate details")
    col1, col2 = st.columns([2, 3])

    with col1:
        st.write("**Drug:**", row["drug"])
        st.write("**Disease:**", row["disease"])
        st.write("**Final score:**", float(row["final_score"]))
        st.write("**Neural score:**", float(row["neural_score"]))
        st.write("**Best path score:**", float(row["best_path_score"]))
        st.write("**Symbolic score:**", float(row["symbolic_score"]))

    with col2:
        st.markdown("**Rule breakdown**")
        st.json({
            "target_in_pathway": row.get("rule_target_in_pathway", 0),
            "bbb_check": row.get("rule_bbb_check", 0),
            "toxicity_ok": row.get("rule_toxicity_ok", 0),
            "mechanism_consistent": row.get("rule_mechanism_consistent", 0),
            "meta_path_score": row.get("rule_meta_path_score", 0),
        })

    # Prepare path (split by " | " which aggregate_scores writes)
    raw_path = str(row.get("best_path", ""))
    if raw_path.strip() == "":
        path: List[str] = []
    else:
        # support both "A | B | C" and comma/arrow separated variants
        if " | " in raw_path:
            path = [p.strip() for p in raw_path.split(" | ") if p.strip()]
        elif "->" in raw_path:
            path = [p.strip() for p in raw_path.split("->") if p.strip()]
        else:
            # fallback: single node or whitespace-separated
            path = [raw_path.strip()] if raw_path.strip() else []

    st.markdown("### Path visualization ")

    if not path:
        st.info("No supporting path available for this candidate.")
    else:
        try:
            dot = graphviz.Digraph(engine="dot")
            # Add nodes and colored labels heuristically
            for i, node in enumerate(path):
                # choose simple style by keywords
                label = node
                if i == 0:
                    dot.node(str(i), label=label, shape="box", style="filled", fillcolor="#1f77b4", fontcolor="white")
                elif i == len(path) - 1:
                    dot.node(str(i), label=label, shape="oval", style="filled", fillcolor="#d62728", fontcolor="white")
                else:
                    # intermediate nodes
                    dot.node(str(i), label=label, shape="ellipse", style="filled", fillcolor="#ffdd99")
                if i > 0:
                    dot.edge(str(i - 1), str(i))
            st.graphviz_chart(dot)
        except Exception as e:
            st.warning("Graph visualization failed — showing textual path instead.")
            st.write("Error from graphviz:", str(e))
            st.markdown("**Path (fallback view):**")
            st.write(" → ".join(path))
            # also show monospace rendering
            st.markdown(f"```\n{' -> '.join(path)}\n```")

    # Explanation section (simple)
    st.markdown("### Mechanistic explanation")
    # Build a short sentence from path nodes when available
    if path and len(path) >= 2:
        drug_node = path[0]
        last_node = path[-1]
        middle = " → ".join(path[1:-1]) if len(path) > 2 else ""
        rationale = f"This path connects **{drug_node}** to **{last_node}** via {middle if middle else 'direct interaction'}."
    else:
        rationale = "No mechanistic path available to generate an explanation."

    st.write(rationale)

    # Optional: show raw row for debugging
    with st.expander("Raw candidate record"):
        st.write(row.to_dict())
