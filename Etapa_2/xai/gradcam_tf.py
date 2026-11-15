"""Grad-CAM en TensorFlow para HCR-Net (mismos casos y misma figura que gradcam_torch.py), con el modelo
de results/modelos/<run>.keras que train_hcrnet.py guarda desde la mejor época.
"""

import argparse
import csv
import sys
from pathlib import Path

import keras
import matplotlib
import numpy as np
import tensorflow as tf

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import PROCESSED_DIR, RESULTS_DIR, load_data, subclass_to_word

MODELS_DIR = RESULTS_DIR / "modelos"
FIGURES_DIR = RESULTS_DIR / "figuras"
PREDS_DIR = RESULTS_DIR / "preds"
RUNS = ("hcrnet_sinaug", "hcrnet_aug", "hcrnet_aug_elastica")
N_CASOS = 6
SIZE_DISPLAY = 64
TITULOS_FILAS = ["aciertos con mayor conf", "aciertos con menor conf", "errores con mayor conf"]


def ultima_conv(model):
    """El objetivo de Grad-CAM: la última convolucional del recorte de VGG16, block4_conv2."""
    conv = None
    for layer in model.layers:
        if layer.__class__.__name__ == "Conv2D":
            conv = layer
    return conv


def calcular_cam(model, grad_model, x, clase_idx, size_out):
    """Un forward y un backward con tape: los canales se ponderan por el gradiente medio espacial."""
    with tf.GradientTape() as tape:
        activacion, salida = grad_model(x, training=False)
        logit = salida[0, clase_idx]
    grads = tape.gradient(logit, activacion)
    pesos = tf.reduce_mean(grads, axis=(0, 1))
    mapa = tf.nn.relu(tf.reduce_sum(activacion[0] * pesos, axis=-1))
    maximo = tf.reduce_max(mapa)
    if maximo > 0:
        mapa = mapa / maximo
    mapa = tf.image.resize(mapa[None, ..., None], size_out, method="bilinear")[0, ..., 0]
    return mapa.numpy()


def clase_explicada(model, x, palabra, M, words):
    """La subclase con mayor probabilidad dentro de la palabra elegida: a la salida las
    probabilidades de las subclases se suman por palabra."""
    proba = model.predict(x, verbose=0)[0]
    idx_palabra = int(np.where(words == palabra)[0][0])
    idx_subclases = np.where(M[:, idx_palabra])[0]
    return int(idx_subclases[np.argmax(proba[idx_subclases])])


def read_preds(path, split):
    with open(path) as f:
        rows = [r for r in csv.DictReader(f) if r["split"] == split]
    for r in rows:
        r["conf"] = float(r["conf"])
    return rows


def seleccionar(rows, n):
    ok = [r for r in rows if r["y_pred"] == r["y_true"]]
    return [sorted(ok, key=lambda r: -r["conf"])[:n],
            sorted(ok, key=lambda r: r["conf"])[:n],
            sorted((r for r in rows if r["y_pred"] != r["y_true"]),
                   key=lambda r: -r["conf"])[:n]]


def figura(casos, camas_f, nombre_capa, titulo, run, images):
    """Filas de casos con la imagen en tinta y el mapa de la capa superpuesto."""
    filas, n = len(casos), len(casos[0])
    fig, axes = plt.subplots(filas, n, figsize=(2.0 * n, 2.55 * filas), squeeze=False)
    for f_ in range(filas):
        for c_ in range(n):
            ax = axes[f_, c_]
            r = casos[f_][c_]
            ax.imshow(images[r["id"]], cmap="gray_r", vmin=0, vmax=255)
            # el alfa sigue al mapa: las zonas frías dejan ver el trazo y solo resaltan las calientes
            ax.imshow(camas_f[f_][c_], cmap="jet", alpha=0.1 + 0.55 * camas_f[f_][c_])
            ax.set_title(f"{r['y_true']} → {r['y_pred']}\nconf {r['conf']:.2f}", fontsize=8)
            ax.axis("off")
    for f_, fila_titulo in enumerate(TITULOS_FILAS):
        fig.text(0.012, (filas - f_ - 0.5) / filas, fila_titulo, rotation=90, va="center",
                 ha="left", fontsize=8.5, color="#52514e")
    fig.suptitle(titulo, x=0.08, ha="left", fontsize=11)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"gradcam_{run}_{nombre_capa}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", choices=RUNS, default="hcrnet_aug")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--split", choices=["val", "test"], default="test")
    parser.add_argument("--n", type=int, default=N_CASOS, help="casos por fila")
    parser.add_argument("--weights", help="ruta al .keras (por defecto results/modelos/<run>.keras)")
    args = parser.parse_args()

    keras.utils.set_random_seed(args.seed)
    run = f"{args.run}_seed{args.seed}"
    path_weights = Path(args.weights) if args.weights else MODELS_DIR / f"{run}.keras"
    if not path_weights.exists():
        sys.exit(f"no existe {path_weights}; entrena la corrida sin --search para que train_hcrnet.py la guarde")

    model = keras.models.load_model(path_weights)
    conv = ultima_conv(model)
    grad_model = keras.Model(model.inputs, [conv.output, model.output])

    X, meta = load_data(32)
    X = X[..., None].astype("float32") / 255
    subclases = np.array(sorted(set(meta["subclase"])))
    M, words = subclass_to_word(subclases)

    rows = read_preds(PREDS_DIR / f"{run}.csv", args.split)
    casos = seleccionar(rows, args.n)
    d64 = np.load(PROCESSED_DIR / "glifos64.npz")
    images = dict(zip(d64["ids"], d64["X"]))

    camas_f = [[] for _ in range(3)]
    for f_, casos_fila in enumerate(casos):
        for r in casos_fila:
            i = int(np.where(meta["id"] == r["id"])[0][0])
            x = X[i:i + 1]
            clase_idx = clase_explicada(model, x, r["y_pred"], M, words)
            cam = calcular_cam(model, grad_model, x, clase_idx, (SIZE_DISPLAY, SIZE_DISPLAY))
            camas_f[f_].append(cam)
            print(f"{TITULOS_FILAS[f_]}: {r['y_true']} → {r['y_pred']} (conf {r['conf']:.2f}, "
                  f"id {r['id']}, explica {subclases[clase_idx]})")

    titulo = f"Grad-CAM {run} ({conv.name})"
    path = figura(casos, camas_f, conv.name, titulo, run, images)
    print(f"-> {path}")


if __name__ == "__main__":
    main()
