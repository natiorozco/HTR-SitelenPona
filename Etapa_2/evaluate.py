"""Calcula las métricas de todos los modelos en results/preds/ (media ± desv. entre semillas)."""

import argparse
import csv
import re
from collections import defaultdict

import numpy as np
from sklearn.metrics import f1_score

from common import PREDS_DIR, RESULTS_DIR

METRICS = ["top1", "top3", "top5", "macro_f1"]


def score(path, split):
    with open(path) as f:
        rows = [r for r in csv.DictReader(f) if r["split"] == split]
    y_true = [r["y_true"] for r in rows]
    y_pred = [r["y_pred"] for r in rows]
    top = [r["top5"].split("|") for r in rows]
    result = {f"top{k}": np.mean([t in tk[:k] for t, tk in zip(y_true, top)]) for k in (1, 3, 5)}
    result["macro_f1"] = f1_score(y_true, y_pred, average="macro")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["val", "test"], default="test")
    args = parser.parse_args()

    by_model = defaultdict(list)
    for path in sorted(PREDS_DIR.glob("*_seed*.csv")):
        model = re.sub(r"_seed\d+$", "", path.stem)
        by_model[model].append(score(path, args.split))

    out = RESULTS_DIR / f"metricas_{args.split}.csv"
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["modelo", "n_semillas"] + [f"{m}_{s}" for m in METRICS for s in ("media", "desv")])
        print(f"{'modelo':24s} n  " + "  ".join(f"{m:>15s}" for m in METRICS))
        for model, runs in by_model.items():
            means = [np.mean([r[m] for r in runs]) for m in METRICS]
            stds = [np.std([r[m] for r in runs]) for m in METRICS]
            writer.writerow([model, len(runs)] + [f"{v:.4f}" for pair in zip(means, stds) for v in pair])
            print(f"{model:24s} {len(runs)}  " + "  ".join(
                f"{mu:7.2%} ±{sd:5.2%}" for mu, sd in zip(means, stds)))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
