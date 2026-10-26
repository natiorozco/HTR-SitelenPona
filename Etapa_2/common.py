"""Funciones que comparten todos los modelos: cargar los datos y guardar resultados.
"""

import csv
import json
import platform
import re
from pathlib import Path

import numpy as np

ETAPA2 = Path(__file__).resolve().parent
PROCESSED_DIR = ETAPA2 / "data" / "processed"
RESULTS_DIR = ETAPA2 / "results"
PREDS_DIR = RESULTS_DIR / "preds"
LOGS_DIR = RESULTS_DIR / "logs"


def load_data(size=32):
    data = np.load(PROCESSED_DIR / f"glifos{size}.npz")
    with open(PROCESSED_DIR / "splits.csv") as f:
        rows = list(csv.DictReader(f))
    meta = {key: np.array([r[key] for r in rows]) for key in ("id", "subclase", "clase", "split")}
    assert (data["ids"] == meta["id"]).all(), "glifos.npz y splits.csv no están alineados"
    return data["X"], meta


def subclass_to_word(subclases):
    """Matriz para sumar las probabilidades de las subclases de una misma palabra."""
    word_of = [re.sub(r"_\d+$", "", s) for s in subclases]
    words = sorted(set(word_of))
    M = np.zeros((len(word_of), len(words)))
    for i, w in enumerate(word_of):
        M[i, words.index(w)] = 1
    return M, np.array(words)


def write_preds(model_name, seed, ids, splits, y_true_words, proba, subclases):
    M, words = subclass_to_word(subclases)
    word_proba = proba @ M
    top5 = np.argsort(-word_proba, axis=1)[:, :5]
    PREDS_DIR.mkdir(parents=True, exist_ok=True)
    path = PREDS_DIR / f"{model_name}_seed{seed}.csv"
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "split", "y_true", "y_pred", "conf", "top5"])
        for i in range(len(ids)):
            writer.writerow([ids[i], splits[i], y_true_words[i], words[top5[i, 0]],
                             f"{word_proba[i, top5[i, 0]]:.4f}", "|".join(words[top5[i]])])
    return path


def write_log(name, info):
    path = LOGS_DIR / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    info = {"hardware": {"plataforma": platform.platform(), "cpu": platform.processor(),
                         "python": platform.python_version()}, **info}
    with open(path, "w") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
