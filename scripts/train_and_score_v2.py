#!/usr/bin/env python3
"""
Compatibility-safe training + scoring with PyKEEN.
Uses the minimal pipeline() call to avoid version-specific kwargs.
"""
from pathlib import Path
import pandas as pd
from pykeen.pipeline import pipeline

ROOT = Path.cwd()
TRIPLES = ROOT / "data" / "kg_triples.csv"
MODEL_DIR = ROOT / "models" / "complex-model"
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True, parents=True)

def train_model(epochs=10):
    print("Training ComplEx model on", TRIPLES)
    # minimal pipeline call to maximize compatibility
    result = pipeline(
        training=str(TRIPLES),
        model='ComplEx',
        epochs=epochs,
        device='cpu',
        random_seed=42,
    )
    # try to save the result if API supports it
    try:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        result.save_to_directory(str(MODEL_DIR))
        print("Saved training result to", MODEL_DIR)
    except Exception:
        print("Could not save result directory (API variation). Continuing.")
    return result

def load_nodes():
    nfile = ROOT / "data" / "node_lookup.csv"
    if not nfile.exists():
        raise FileNotFoundError(nfile)
    df = pd.read_csv(nfile, dtype=str)
    drugs = df[df['prefix']=='Drug']['node_key'].tolist()
    diseases = df[df['prefix']=='Disease']['node_key'].tolist()
    return drugs, diseases

def score_pairs(result, drugs, diseases):
    model = result.model
    relation = 'treats'
    rows = []
    for d in drugs:
        for dis in diseases:
            try:
                score = float(model.predict_hrt([(d, relation, dis)])[0])
            except Exception:
                score = 0.0
            rows.append((d.split(":",1)[1], dis.split(":",1)[1], score))
    df = pd.DataFrame(rows, columns=['drug','disease','score'])
    if not df['score'].isnull().all():
        mn, mx = df['score'].min(), df['score'].max()
        if mx > mn:
            df['score'] = (df['score'] - mn) / (mx - mn)
        else:
            df['score'] = 0.0
    out = ARTIFACTS / "global_scores.csv"
    df.to_csv(out, index=False)
    print("Wrote neural scores to", out)
    return out

if __name__ == "__main__":
    # default to small number of epochs for a quick run
    res = train_model(epochs=10)
    drugs, diseases = load_nodes()
    score_pairs(res, drugs, diseases)
