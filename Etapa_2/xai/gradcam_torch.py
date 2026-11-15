"""Grad-CAM en PyTorch para SimpleCNN y ResNet18, sobre aciertos, errores y casos de baja confianza de
una corrida ya entrenada (carga results/modelos/<run>.pt, que train.py guarda desde la mejor época).
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import torch
import torch.nn.functional as F

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "torch_models"))
from common import PROCESSED_DIR, RESULTS_DIR, load_data, subclass_to_word
from models import MODELS

MODELS_DIR = RESULTS_DIR / "modelos"
FIGURES_DIR = RESULTS_DIR / "figuras"
PREDS_DIR = RESULTS_DIR / "preds"
N_CASOS = 6
SIZE_DISPLAY = 64
# con entrada de 64 px, layer4 de ResNet18 deja un mapa de 2x2 y layer3 uno de 4x4; se grafican las
# dos para comparar la legibilidad y que la discusión declare cuál sirve
LAYERS = {
    "cnn": {"relu3": lambda m: m.features[2][5]},
    "resnet18": {"layer4": lambda m: m.net.layer4, "layer3": lambda m: m.net.layer3},
}
TITULOS_FILAS = ["aciertos con mayor conf", "aciertos con menor conf", "errores con mayor conf"]


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


class Capturas:
    """Registra las activaciones de las capas objetivo en cada forward."""

    def __init__(self, model, model_name):
        self.activaciones, self.nombres = [], []
        for nombre, captura in LAYERS[model_name].items():
            captura(model).register_forward_hook(self._guardar(nombre))

    def _guardar(self, nombre):
        def hook(module, entrada, salida):
            # en cálculo sin gradiente (selección del logit explicado) el tensor no permite retain_grad
            if salida.requires_grad:
                salida.retain_grad()
            self.activaciones.append(salida)
            self.nombres.append(nombre)
        return hook

    def limpiar(self):
        self.activaciones.clear()
        self.nombres.clear()


def calcular_cams(model, x, capturas, size_out):
    """Un forward y un backward: el mapa pondera los canales por el gradiente medio espacial del logit."""
    model.zero_grad()
    logits = model(x.unsqueeze(0))[0]
    logits[int(logits.argmax())].backward()
    cams = {}
    for nombre, activacion in zip(capturas.nombres, capturas.activaciones):
        pesos = activacion.grad.mean(dim=(2, 3), keepdim=True)
        mapa = torch.relu((activacion * pesos).sum(1)).squeeze(0)
        maximo = mapa.max()
        if maximo > 0:
            mapa = mapa / maximo
        # el mapa se sube a la resolución de visualización para superponerlo sobre la imagen
        cams[nombre] = F.interpolate(mapa[None, None].float(), size=size_out, mode="bilinear",
                                     align_corners=False)[0, 0].detach().cpu().numpy()
    return cams


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


def figura(casos, cams_f, nombre_capa, titulo, run, images):
    """Filas de casos con la imagen en tinta y el mapa de la capa superpuesto."""
    filas, n = len(casos), len(casos[0])
    fig, axes = plt.subplots(filas, n, figsize=(2.0 * n, 2.55 * filas), squeeze=False)
    for f_ in range(filas):
        for c_ in range(n):
            ax = axes[f_, c_]
            r = casos[f_][c_]
            ax.imshow(images[r["id"]], cmap="gray_r", vmin=0, vmax=255)
            # el alfa sigue al mapa: las zonas frías dejan ver el trazo y solo resaltan las calientes
            ax.imshow(cams_f[f_][c_], cmap="jet", alpha=0.1 + 0.55 * cams_f[f_][c_])
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
    parser.add_argument("--model", choices=MODELS, default="cnn")
    parser.add_argument("--aug", choices=["none", "trad"], default="none")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--split", choices=["val", "test"], default="test")
    parser.add_argument("--n", type=int, default=N_CASOS, help="casos por fila")
    parser.add_argument("--weights", help="ruta al .pt (por defecto results/modelos/<run>.pt)")
    args = parser.parse_args()

    device = get_device()
    torch.manual_seed(args.seed)
    model_cls, size = MODELS[args.model]
    name = f"{args.model}_{'aug' if args.aug == 'trad' else 'sinaug'}"
    run = f"{name}_seed{args.seed}"

    path_weights = Path(args.weights) if args.weights else MODELS_DIR / f"{run}.pt"
    if not path_weights.exists():
        sys.exit(f"no existe {path_weights}; entrena la corrida sin --search para que train.py la guarde")

    X, meta = load_data(size)
    with open(PROCESSED_DIR / f"norm_stats{size}.json") as f:
        stats = json.load(f)
    subclases = np.array(sorted(set(meta["subclase"])))
    M, words = subclass_to_word(subclases)

    model = model_cls(len(subclases))
    model.load_state_dict(torch.load(path_weights, map_location=device))
    model.eval().to(device)
    capturas = Capturas(model, args.model)

    rows = read_preds(PREDS_DIR / f"{run}.csv", args.split)
    casos = seleccionar(rows, args.n)

    X_t = torch.from_numpy(X).float().div(255).unsqueeze(1)
    mean = torch.tensor(stats["mean"], device=device)
    std = torch.tensor(stats["std"], device=device)
    d64 = np.load(PROCESSED_DIR / "glifos64.npz")
    images = dict(zip(d64["ids"], d64["X"]))

    nombres = list(LAYERS[args.model])
    cams_f = {nombre: [[] for _ in range(3)] for nombre in nombres}
    for f_, casos_fila in enumerate(casos):
        for r in casos_fila:
            i = int(np.where(meta["id"] == r["id"])[0][0])
            x = (X_t[i].to(device) - mean) / std
            capturas.limpiar()
            with torch.no_grad():
                logits = model(x.unsqueeze(0))[0].cpu().numpy()
            # el logit explicado es la subclase con mayor valor dentro de la palabra que eligió el
            # modelo: a la salida las probabilidades de las subclases se suman por palabra
            idx_palabra = int(np.where(words == r["y_pred"])[0][0])
            idx_subclases = np.where(M[:, idx_palabra])[0]
            clase_idx = int(idx_subclases[np.argmax(logits[idx_subclases])])
            capturas.limpiar()
            cams = calcular_cams(model, x, capturas, (SIZE_DISPLAY, SIZE_DISPLAY))
            for nombre in nombres:
                cams_f[nombre][f_].append(cams[nombre])
            print(f"{TITULOS_FILAS[f_]}: {r['y_true']} → {r['y_pred']} (conf {r['conf']:.2f}, "
                  f"id {r['id']}, explica {subclases[clase_idx]})")

    for nombre in nombres:
        titulo = f"Grad-CAM {run} ({nombre})"
        path = figura(casos, cams_f[nombre], nombre, titulo, run, images)
        print(f"-> {path}")


if __name__ == "__main__":
    main()
