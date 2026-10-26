"""Baseline clásico: HOG (o pixeles crudos) + regresión logística.

Los hiperparámetros se eligen por macro-F1 en validación y test se predice una sola vez.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
from skimage.feature import hog
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import load_data, subclass_to_word, write_log, write_preds

SEED = 0
C_GRID = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]
CELL_GRID = [4, 8, 16] 


def extract(features, cell):
    if features == "hog":
        X, meta = load_data(64)
        feats = np.stack([hog(x, orientations=9, pixels_per_cell=(cell, cell),
                              cells_per_block=(2, 2)) for x in X])
    else:
        X, meta = load_data(32)
        feats = X.reshape(len(X), -1) / 255.0
    return feats, meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", choices=["hog", "pixels"], default="hog")
    args = parser.parse_args()
    name = f"{args.features}_lr"

    search, best = [], None
    for cell in CELL_GRID if args.features == "hog" else [None]:
        feats, meta = extract(args.features, cell)
        train, val = meta["split"] == "train", meta["split"] == "val"
        print(f"{name} (celda {cell}): {feats.shape[1]} características")
        for C in C_GRID:
            start = time.perf_counter()
            model = make_pipeline(StandardScaler(),
                                  LogisticRegression(C=C, max_iter=2000, random_state=SEED))
            model.fit(feats[train], meta["subclase"][train])
            seconds = time.perf_counter() - start
            M, words = subclass_to_word(model.classes_)
            val_pred = words[(model.predict_proba(feats[val]) @ M).argmax(axis=1)]
            f1 = f1_score(meta["clase"][val], val_pred, average="macro")
            search.append({"celda": cell, "C": C, "val_macro_f1": round(f1, 4),
                           "segundos_ajuste": round(seconds, 1)})
            print(f"  C={C:<6} val macro-F1={f1:.4f}  ({seconds:.0f} s)")
            if best is None or f1 > best["f1"]:
                best = {"f1": f1, "celda": cell, "C": C, "model": model, "feats": feats}

    print(f"  elegido: celda {best['celda']}, C={best['C']}")
    model = best["model"]
    path = write_preds(name, SEED, meta["id"], meta["split"], meta["clase"],
                       model.predict_proba(best["feats"]), model.classes_)
    write_log(name, {"modelo": name, "semilla": SEED, "features": args.features,
                     "criterio_seleccion": "macro-F1 en validación", "busqueda": search,
                     "elegido": {"celda": best["celda"], "C": best["C"]}})
    print(f"  -> {path.name}")


if __name__ == "__main__":
    main()
