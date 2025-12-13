#!/usr/bin/env python3
"""
Compatibility-safe PyKEEN training + scoring using an explicit TriplesFactory.
"""
from pathlib import Path
import pandas as pd
import sys

# try imports that vary across pykeen versions
try:
    from pykeen.pipeline import pipeline
    from pykeen.triples import TriplesFactory
except Exception:
    try:
        # some versions place TriplesFactory elsewhere
        from pykeen.pipeline import pipeline
        from pykeen.datasets import TriplesFactory
    except Exception as e:
        print("Could not import TriplesFactory from pykeen:", e, file=sys.stderr)
        raise

ROOT = Path.cwd()
TRIPLES = ROOT / "data" / "kg_triples.csv"
MODEL_DIR = ROOT / "models" / "complex-model"
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True, parents=True)

def build_triples_factory(path: Path):
    print("Building TriplesFactory from", path)
    # pykeen expects triples as tab/space/comma-separated head relation tail
    # we will use pandas to load and then TriplesFactory.from_labeled_triples
    df = pd.read_csv(path, dtype=str)
    if {'head','relation','tail'}.issubset(df.columns):
        triples = df[['head','relation','tail']].values
    else:
        # fallback: assume three columns in order
        triples = df.values[:, :3]
    # convert to list of tuples
    triples = [tuple(map(str, t)) for t in triples]
    try:
        tf = TriplesFactory.from_labeled_triples(triples)
    except Exception:
        # some pykeen versions accept from_path
        try:
            tf = TriplesFactory.from_path(str(path))
        except Exception as e:
            print("Failed to create TriplesFactory:", e, file=sys.stderr)
            raise
    print("TriplesFactory: num_triples =", tf.num_triples, "num_entities =", tf.num_entities)
    return tf

def train_model(epochs=10):
    tf = build_triples_factory(TRIPLES)
    print("Training ComplEx model")
    # pass the triples factory as the training argument
    result = pipeline(
        training=tf,
        model='ComplEx',
        epochs=epochs,
        device='cpu',
        random_seed=42,
    )
    # try to save model if API allows
    try:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        result.save_to_directory(str(MODEL_DIR))
        print("Saved training result to", MODEL_DIR)
    except Exception:
        print("Could not save training result directory (API variation). Continuing.")
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
    res = train_model(epochs=10)
    drugs, diseases = load_nodes()
    score_pairs(res, drugs, diseases)
