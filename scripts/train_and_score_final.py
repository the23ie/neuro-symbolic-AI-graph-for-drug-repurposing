#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory

ROOT = Path.cwd()
TRIPLES = ROOT / "data" / "kg_triples.csv"
NODE_LOOKUP = ROOT / "data" / "node_lookup.csv"
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True, parents=True)

def load_triples():
    df = pd.read_csv(TRIPLES, dtype=str)
    triples = df[['head','relation','tail']].astype(str).values
    triples = np.array(triples, dtype=str)
    tf = TriplesFactory.from_labeled_triples(triples)
    print("Loaded TriplesFactory:", tf.num_triples, "triples,", tf.num_entities, "entities")
    return tf

def train_model(tf, epochs=10):
    print(f"Training ComplEx for {epochs} epochs...")
    # For compatibility with pykeen versions requiring both training/testing,
    # pass the same TriplesFactory as training/testing/validation for this quick run.
    result = pipeline(
        training=tf,
        testing=tf,
        validation=tf,
        model='ComplEx',
        epochs=epochs,
        device='cpu',
        random_seed=42,
    )
    print("Training complete.")
    return result

def load_drugs_and_diseases():
    df = pd.read_csv(NODE_LOOKUP, dtype=str)
    drugs = df[df['prefix']=='Drug']['node_key'].tolist()
    diseases = df[df['prefix']=='Disease']['node_key'].tolist()
    print("Drugs:", len(drugs), "Diseases:", len(diseases))
    return drugs, diseases

def score_pairs(model, drugs, diseases):
    relation = "treats"
    rows = []
    for d in drugs:
        for dis in diseases:
            try:
                score = float(model.predict_hrt([(d, relation, dis)])[0])
            except Exception:
                score = 0.0
            rows.append((d.split(":",1)[1], dis.split(":",1)[1], score))

    df = pd.DataFrame(rows, columns=['drug','disease','score'])
    if df['score'].max() > df['score'].min():
        df['score'] = (df['score'] - df['score'].min()) / (df['score'].max() - df['score'].min())
    else:
        df['score'] = 0.0

    out = ARTIFACTS / "global_scores.csv"
    df.to_csv(out, index=False)
    print("WROTE:", out)
    return out

if __name__ == "__main__":
    tf = load_triples()
    result = train_model(tf, epochs=10)
    drugs, diseases = load_drugs_and_diseases()
    score_pairs(result.model, drugs, diseases)
