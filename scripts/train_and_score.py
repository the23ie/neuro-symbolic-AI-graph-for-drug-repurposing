# scripts/train_and_score.py
import os
from pathlib import Path
import pandas as pd
from pykeen.pipeline import pipeline
from pykeen.models.predict import get_tail_prediction_df, get_head_prediction_df

ROOT = Path.cwd()
TRIPLES = ROOT / "data" / "kg_triples.csv"
MODEL_DIR = ROOT / "models" / "complex-model"
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True, parents=True)

def train_model():
    print("Training ComplEx model on", TRIPLES)
    result = pipeline(
        training= str(TRIPLES),
        model='ComplEx',
        loss='BCEWithLogitsLoss',  # stable for multi-relational
        training_loop='slcwa',
        epochs=100,
        random_seed=42,
        device='cpu',  # change to 'cuda' if GPU enabled
        output_path=str(MODEL_DIR),
        optimizer='Adam',
        optimizer_kwargs=dict(lr=1e-3),
        training_kwargs=dict(batch_size=256),
        stopper=None,
        create_inverse_triples=False,
        save_best_model=True,
        evaluation=None,
    )
    print("Training done. Model dir:", MODEL_DIR)
    return result

def load_nodes():
    # node_lookup.csv contains node_key like "Drug:metformin"
    nfile = ROOT / "data" / "node_lookup.csv"
    if not nfile.exists():
        raise FileNotFoundError(nfile)
    df = pd.read_csv(nfile, dtype=str)
    # select drug and disease nodes
    drugs = df[df['prefix']=='Drug']['node_key'].tolist()
    diseases = df[df['prefix']=='Disease']['node_key'].tolist()
    return drugs, diseases

def score_pairs(result, drugs, diseases):
    model = result.model
    # to score arbitrary (drug, disease) pairs, we assume relation label 'treats' exists in your KG
    relation = 'treats'
    rows = []
    for d in drugs:
        for dis in diseases:
            try:
                # predict score for triple (head=d, relation, tail=dis)
                score = model.predict_hrt([ (d, relation, dis) ])[0]
            except Exception:
                # if the relation label doesn't exist in training, skip
                score = 0.0
            rows.append((d.split(":",1)[1], dis.split(":",1)[1], float(score)))
    df = pd.DataFrame(rows, columns=['drug','disease','score'])
    # normalize 0..1
    if not df['score'].isnull().all():
        mn, mx = df['score'].min(), df['score'].max()
        if mx>mn:
            df['score'] = (df['score'] - mn) / (mx - mn)
        else:
            df['score'] = 0.0
    out = ARTIFACTS / "global_scores.csv"
    df.to_csv(out, index=False)
    print("Wrote neural scores to", out)
    return out

if __name__ == "__main__":
    result = train_model()
    drugs, diseases = load_nodes()
    score_pairs(result, drugs, diseases)
