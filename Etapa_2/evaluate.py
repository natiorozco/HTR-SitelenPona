"""Calcula las métricas de todos los modelos en results/preds/ (media ± desv. entre semillas) y genera
el análisis de resultados: curvas, diagnóstico de sobreajuste, confusiones, errores y tabla de referencias.
"""

import argparse
import csv
import json
import re
from collections import Counter, defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import f1_score

from common import LOGS_DIR, PREDS_DIR, RESULTS_DIR, load_data

METRICS = ["top1", "top3", "top5", "macro_f1"]
FIGURES_DIR = RESULTS_DIR / "figuras"
TRAIN_COLOR, VAL_COLOR, MUTED = "#2a78d6", "#eb6834", "#8a8984"
N_PARES = 15
N_ERRORES = 24
# rol de cada modelo en la comparación, según el prefijo de su nombre
ROLES = [("dummy", "trivial"), ("pixels_lr", "clásica (ablación)"), ("hog_lr", "clásica"),
         ("hcrnet", "literatura"), ("cnn", "propia"), ("resnet18", "propia")]
PUBLICADOS = """\
**Valores publicados (no directamente comparables).** HCR-Net reporta 99.31 % de exactitud en
HWRGurmukhi_1.1 (35 clases, un escritor, 100 muestras por clase) y 96.53 % en HWRGurmukhi_1.3
(35 clases, 100 escritores, una muestra por clase y escritor), con partición aleatoria 80:20 y la
exactitud de la última época. La CNN de Rahman et al. reporta 85.96 % en bengalí (50 clases, ~400
muestras por clase). Aquí hay 132 palabras, 52–133 muestras por clase, partición agrupada por sesión y
selección de época por validación, así que esos números sirven como orden de magnitud, no como
comparación directa. Las cifras publicadas son exactitud top-1, no macro-F1.
"""


def read_preds(path, split):
    with open(path) as f:
        return [r for r in csv.DictReader(f) if r["split"] == split]


def score(rows):
    y_true = [r["y_true"] for r in rows]
    y_pred = [r["y_pred"] for r in rows]
    top = [r["top5"].split("|") for r in rows]
    result = {f"top{k}": np.mean([t in tk[:k] for t, tk in zip(y_true, top)]) for k in (1, 3, 5)}
    result["macro_f1"] = f1_score(y_true, y_pred, average="macro")
    return result


def role(model):
    return next((r for prefix, r in ROLES if model.startswith(prefix)), "otra")


def style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e4e3df", linewidth=0.8)
    ax.set_axisbelow(True)


def tabla_referencias(summary, split):
    """Tabla en Markdown contra las tres referencias (trivial, clásica y literatura) y los modelos propios."""
    order = [r for _, r in ROLES]
    models = sorted(summary, key=lambda m: (order.index(role(m)) if role(m) in order else len(order), m))
    ref = summary.get("hog_lr", {}).get("macro_f1", (None,))[0]
    fmt = lambda mu, sd: f"{mu:.2%} ± {sd:.2%}"
    lines = [f"| Referencia | Modelo | Semillas | Top-1 | Top-5 | Macro-F1 | Δ macro-F1 vs HOG + LR |",
             "|---|---|---|---|---|---|---|"]
    for m in models:
        s = summary[m]
        delta = "—" if ref is None or m == "hog_lr" else f"{(s['macro_f1'][0] - ref) * 100:+.2f} pp"
        lines.append(f"| {role(m)} | {m} | {s['n']} | {fmt(*s['top1'])} | {fmt(*s['top5'])} | "
                     f"{fmt(*s['macro_f1'])} | {delta} |")
    path = RESULTS_DIR / f"tabla_referencias_{split}.md"
    path.write_text(f"# Comparación contra las referencias ({split})\n\n" + "\n".join(lines)
                    + "\n\n" + PUBLICADOS, encoding="utf-8")
    return path


def curvas(model):
    """Curvas de la semilla más baja y diagnóstico de sobreajuste de todas las semillas."""
    diag, first = [], None
    for path in sorted(LOGS_DIR.glob(f"{model}_seed*.json")):
        with open(path, encoding="utf-8") as f:
            log = json.load(f)
        h = log.get("historial")
        if not h:
            continue
        first = first or log
        b = h[log["mejor_epoca"] - 1]
        diag.append({"modelo": model, "semilla": log["semilla"], "mejor_epoca": log["mejor_epoca"],
                     "epocas_corridas": len(h), "train_acc": b["train_acc"], "val_acc": b["val_acc"],
                     "brecha_acc": b["train_acc"] - b["val_acc"], "train_loss": b["train_loss"],
                     "val_loss": b["val_loss"], "subida_val_loss": h[-1]["val_loss"] - b["val_loss"]})
    if first is None:
        return diag

    h, best = first["historial"], first["mejor_epoca"]
    epochs = [e["epoca"] for e in h]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, key, label in zip(axes, ("loss", "acc"), ("Pérdida", "Exactitud")):
        ax.plot(epochs, [e[f"train_{key}"] for e in h], color=TRAIN_COLOR, lw=2, label="train")
        ax.plot(epochs, [e[f"val_{key}"] for e in h], color=VAL_COLOR, lw=2, label="val")
        ax.axvline(best, color=MUTED, ls="--", lw=1)
        ax.annotate(f"mejor época {best}", (best, 1), xycoords=("data", "axes fraction"),
                    xytext=(4, 2), textcoords="offset points", color="#52514e", fontsize=8)
        fase2 = next((e["epoca"] for e in h if e.get("fase") == 2), None)
        if fase2:
            ax.axvspan(fase2 - 0.5, epochs[-1] + 0.5, color="#f1f0ec", zorder=0)
            ax.annotate("fase 2", (fase2, 0), xycoords=("data", "axes fraction"),
                        xytext=(4, 4), textcoords="offset points", color="#52514e", fontsize=8)
        ax.set_xlabel("época")
        ax.set_title(label, loc="left", fontsize=10)
        style(ax)
    axes[0].legend(frameon=False)
    fig.suptitle(f"{model} (semilla {first['semilla']})", x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"curvas_{model}.png", dpi=150)
    plt.close(fig)
    return diag


def confusiones(model, runs, split):
    """Pares más confundidos (sumando todas las semillas) y la submatriz de esas clases."""
    pares, n_true = Counter(), Counter()
    for rows in runs:
        for r in rows:
            n_true[r["y_true"]] += 1
            if r["y_pred"] != r["y_true"]:
                pares[(r["y_true"], r["y_pred"])] += 1
    top = pares.most_common(N_PARES)
    with open(RESULTS_DIR / f"confusiones_{model}_{split}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["real", "predicha", "errores", "tasa", "errores_inversos"])
        for (a, b), n in top:
            writer.writerow([a, b, n, f"{n / n_true[a]:.4f}", pares[(b, a)]])
    if not top:
        return top

    clases = list(dict.fromkeys(c for pair, _ in top for c in pair))
    sub = np.zeros((len(clases), len(clases)))
    for rows in runs:
        for r in rows:
            if r["y_true"] in clases and r["y_pred"] in clases:
                sub[clases.index(r["y_true"]), clases.index(r["y_pred"])] += 1
    sub /= np.array([n_true[c] for c in clases])[:, None]

    size = 0.42 * len(clases) + 2
    fig, ax = plt.subplots(figsize=(size + 1, size))
    im = ax.imshow(sub, cmap="Blues", vmin=0, vmax=1)
    for i, j in zip(*np.nonzero(sub >= 0.01)):
        ax.text(j, i, f"{sub[i, j]:.0%}", ha="center", va="center", fontsize=7,
                color="white" if sub[i, j] > 0.6 else "#0b0b0b")
    ax.set_xticks(range(len(clases)), clases, rotation=90)
    ax.set_yticks(range(len(clases)), clases)
    ax.set_xlabel("predicha")
    ax.set_ylabel("real")
    ax.set_title(f"{model}: clases de los {len(top)} pares más confundidos ({split}, "
                 f"{len(runs)} semilla{'s' if len(runs) > 1 else ''})", loc="left", fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.04, label="fracción de las muestras de la clase real")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"confusion_{model}_{split}.png", dpi=150)
    plt.close(fig)
    return top


def errores(model, rows, images, split):
    """Grilla de los errores con mayor confianza de una semilla."""
    errs = sorted((r for r in rows if r["y_pred"] != r["y_true"]), key=lambda r: -float(r["conf"]))
    errs = errs[:N_ERRORES]
    if not errs:
        return
    cols = 6
    fig, axes = plt.subplots(-(-len(errs) // cols), cols, figsize=(cols * 1.6, -(-len(errs) // cols) * 1.9),
                             squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for ax, r in zip(axes.flat, errs):
        ax.imshow(images[r["id"]], cmap="gray_r", vmin=0, vmax=255)
        ax.set_title(f"{r['y_true']} → {r['y_pred']}\nconf {float(r['conf']):.2f}", fontsize=8)
    fig.suptitle(f"{model}: errores con mayor confianza ({split})", x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"errores_{model}_{split}.png", dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["val", "test"], default="test")
    parser.add_argument("--sin-figuras", action="store_true", help="solo la tabla de métricas")
    args = parser.parse_args()

    by_model = defaultdict(list)
    for path in sorted(PREDS_DIR.glob("*_seed*.csv")):
        by_model[re.sub(r"_seed\d+$", "", path.stem)].append(read_preds(path, args.split))

    summary = {}
    out = RESULTS_DIR / f"metricas_{args.split}.csv"
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["modelo", "n_semillas"] + [f"{m}_{s}" for m in METRICS for s in ("media", "desv")])
        print(f"{'modelo':24s} n  " + "  ".join(f"{m:>15s}" for m in METRICS))
        for model, runs in by_model.items():
            scores = [score(rows) for rows in runs]
            means = [np.mean([s[m] for s in scores]) for m in METRICS]
            stds = [np.std([s[m] for s in scores]) for m in METRICS]
            summary[model] = {"n": len(runs), **{m: (mu, sd) for m, mu, sd in zip(METRICS, means, stds)}}
            writer.writerow([model, len(runs)] + [f"{v:.4f}" for pair in zip(means, stds) for v in pair])
            print(f"{model:24s} {len(runs)}  " + "  ".join(
                f"{mu:7.2%} ±{sd:5.2%}" for mu, sd in zip(means, stds)))
    print(f"-> {out}")
    print(f"-> {tabla_referencias(summary, args.split)}")
    if args.sin_figuras:
        return

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    X, meta = load_data(64)
    images = dict(zip(meta["id"], X))
    diag = []
    for model, runs in by_model.items():
        diag += curvas(model)
        if role(model) == "trivial":
            continue
        top = confusiones(model, runs, args.split)
        errores(model, runs[0], images, args.split)
        print(f"\n{model}: pares más confundidos ({args.split})")
        for (a, b), n in top[:5]:
            print(f"  {a:>10s} → {b:<10s} {n}")

    if diag:
        with open(RESULTS_DIR / "diagnostico_sobreajuste.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(diag[0]))
            writer.writeheader()
            writer.writerows({k: f"{v:.4f}" if isinstance(v, float) else v for k, v in d.items()}
                             for d in diag)
        print("\ndiagnóstico de sobreajuste en la mejor época (media entre semillas)")
        for model in dict.fromkeys(d["modelo"] for d in diag):
            ds = [d for d in diag if d["modelo"] == model]
            print(f"  {model:24s} train acc {np.mean([d['train_acc'] for d in ds]):.3f}  "
                  f"val acc {np.mean([d['val_acc'] for d in ds]):.3f}  "
                  f"brecha {np.mean([d['brecha_acc'] for d in ds]):+.3f}  "
                  f"subida val loss tras la mejor {np.mean([d['subida_val_loss'] for d in ds]):+.3f}")
    print(f"-> {FIGURES_DIR}")


if __name__ == "__main__":
    main()
