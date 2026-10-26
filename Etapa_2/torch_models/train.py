"""Entrena un modelo de PyTorch.

Se detiene cuando el macro-F1 de validación deja de mejorar y predice test en la mejor época.
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader, Dataset
from torchvision.transforms import v2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import PROCESSED_DIR, load_data, subclass_to_word, write_log, write_preds
from models import MODELS


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def build_augmentation(aug, size):
    """Mismos rangos que HCR-Net más distorsión elástica.

    No hay volteos porque pueden convertir un glifo en otro.
    """
    if aug == "none":
        return None
    return v2.Compose([
        v2.RandomAffine(degrees=10, translate=(0.05, 0.05), scale=(0.95, 1.05), shear=0.5),
        v2.RandomApply([v2.ElasticTransform(alpha=size / 2, sigma=size / 8)], p=0.5),
    ])


class GlyphDataset(Dataset):
    def __init__(self, X, y, mean, std, transform=None):
        self.X = torch.from_numpy(X).float().div(255).unsqueeze(1)
        self.y = torch.from_numpy(y)
        self.mean, self.std = mean, std
        self.transform = transform

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        x = self.X[i]
        if self.transform is not None:
            x = self.transform(x)
        return (x - self.mean) / self.std, self.y[i]


@torch.no_grad()
def predict_proba(model, loader, device):
    model.eval()
    return torch.cat([model(x.to(device)).softmax(1).cpu() for x, _ in loader]).numpy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MODELS, default="cnn")
    parser.add_argument("--aug", choices=["none", "trad"], default="none")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--epochs", type=int, default=60, help="máximo de épocas")
    parser.add_argument("--patience", type=int, default=8, help="épocas sin mejorar val macro-F1")
    parser.add_argument("--freeze-epochs", type=int, default=0,
                        help="primeras épocas entrenando solo la última capa")
    parser.add_argument("--search", action="store_true",
                        help="para la búsqueda de hiperparámetros: guarda el log pero no predicciones")
    args = parser.parse_args()

    set_seed(args.seed)
    device = get_device()
    model_cls, size = MODELS[args.model]
    name = f"{args.model}_{'aug' if args.aug == 'trad' else 'sinaug'}"

    X, meta = load_data(size)
    with open(PROCESSED_DIR / f"norm_stats{size}.json") as f:
        stats = json.load(f)
    subclases = np.array(sorted(set(meta["subclase"])))
    y = np.searchsorted(subclases, meta["subclase"])
    M, words = subclass_to_word(subclases)
    train, val = meta["split"] == "train", meta["split"] == "val"

    make = lambda mask, tf: GlyphDataset(X[mask], y[mask], stats["mean"], stats["std"], tf)
    g = torch.Generator().manual_seed(args.seed)
    train_loader = DataLoader(make(train, build_augmentation(args.aug, size)),
                              batch_size=args.batch, shuffle=True, generator=g)
    val_loader = DataLoader(make(val, None), batch_size=256)
    all_loader = DataLoader(make(np.ones(len(y), bool), None), batch_size=256)

    model = model_cls(len(subclases), dropout=args.dropout).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    criterion = nn.CrossEntropyLoss()

    def make_optimizer(params, lr):
        opt = torch.optim.AdamW(params, lr=lr, weight_decay=args.weight_decay)
        sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="max", factor=0.5, patience=3)
        return opt, sched

    # con --freeze-epochs primero se entrena solo la última capa y después toda la red
    frozen = args.freeze_epochs > 0
    optimizer, scheduler = make_optimizer(
        model.head_parameters() if frozen else model.parameters(), args.lr)

    history, best = [], {"f1": -1.0, "epoch": 0, "state": None}
    start = time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        if frozen and epoch == args.freeze_epochs + 1:
            frozen = False
            optimizer, scheduler = make_optimizer(model.parameters(), args.lr / 10)
        model.train()
        loss_sum, correct, seen = 0.0, 0, 0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * len(yb)
            correct += (logits.argmax(1) == yb).sum().item()
            seen += len(yb)

        proba = predict_proba(model, val_loader, device)
        val_loss = nn.functional.nll_loss(torch.log(torch.from_numpy(proba) + 1e-12),
                                          torch.from_numpy(y[val])).item()
        val_pred = words[(proba @ M).argmax(1)]
        val_acc = float((val_pred == meta["clase"][val]).mean())
        val_f1 = f1_score(meta["clase"][val], val_pred, average="macro")
        scheduler.step(val_f1)
        history.append({"epoca": epoch, "train_loss": loss_sum / seen, "train_acc": correct / seen,
                         "val_loss": val_loss, "val_acc": val_acc, "val_macro_f1": val_f1,
                         "lr": optimizer.param_groups[0]["lr"]})
        print(f"época {epoch:3d}  train loss {loss_sum / seen:.3f} acc {correct / seen:.3f}  "
              f"val loss {val_loss:.3f} acc {val_acc:.3f} macro-F1 {val_f1:.3f}")

        if val_f1 > best["f1"]:
            best = {"f1": val_f1, "epoch": epoch,
                    "state": {k: v.detach().clone() for k, v in model.state_dict().items()}}
        elif epoch - best["epoch"] >= args.patience:
            print(f"early stopping: sin mejora desde la época {best['epoch']}")
            break
    train_seconds = time.perf_counter() - start

    model.load_state_dict(best["state"])
    start = time.perf_counter()
    proba = predict_proba(model, all_loader, device)
    ms_per_image = (time.perf_counter() - start) / len(y) * 1000

    run = f"{name}_seed{args.seed}"
    log = {"modelo": name, "semilla": args.seed, "config": vars(args), "dispositivo": str(device),
           "parametros": n_params, "segundos_entrenamiento": round(train_seconds, 1),
           "ms_inferencia_por_imagen": round(ms_per_image, 3),
           "mejor_epoca": best["epoch"], "mejor_val_macro_f1": round(best["f1"], 4),
           "historial": history}
    if args.search:
        tag = f"lr{args.lr}_b{args.batch}_wd{args.weight_decay}"
        write_log(f"busqueda/{run}_{tag}", log)
    else:
        write_log(run, log)
        path = write_preds(name, args.seed, meta["id"], meta["split"], meta["clase"], proba, subclases)
        print(f"-> {path.name}")
    print(f"mejor época {best['epoch']}, val macro-F1 {best['f1']:.4f}, {train_seconds:.0f} s en {device}")


if __name__ == "__main__":
    main()
