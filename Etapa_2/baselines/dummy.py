"""Baseline trivial: clase mayoritaria y predicción aleatoria estratificada."""

import sys
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import load_data, write_preds

SEEDS = [0, 1, 2, 3, 4]


def main():
    X, meta = load_data(32)
    flat = X.reshape(len(X), -1)
    train = meta["split"] == "train"

    # la mayoritaria siempre da lo mismo
    runs = [("dummy_mayoritaria", "most_frequent", 0)]
    runs += [("dummy_estratificada", "stratified", seed) for seed in SEEDS]
    for name, strategy, seed in runs:
        clf = DummyClassifier(strategy=strategy, random_state=seed)
        clf.fit(flat[train], meta["subclase"][train])
        proba = clf.predict_proba(flat)
        if strategy == "stratified":
            # solo da probabilidad a una clase; el resto del top-5 se desempata al azar
            rng = np.random.default_rng(seed)
            proba = proba + rng.random(proba.shape) * 1e-6
        path = write_preds(name, seed, meta["id"], meta["split"], meta["clase"], proba, clf.classes_)
        print(f"{name} seed {seed} -> {path.name}")


if __name__ == "__main__":
    main()
