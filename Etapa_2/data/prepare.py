"""Preprocesa las imágenes del dataset y genera las particiones train/val/test."""

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.model_selection import StratifiedGroupKFold

ETAPA2 = Path(__file__).resolve().parents[1]
RAW_DIR = ETAPA2 / "sitelen-pona-handwritten-png-samples"
OUT_DIR = ETAPA2 / "data" / "processed"

SEED = 42
INK_THRESHOLD = 32      # valor mínimo para contar un píxel como tinta al recortar
MARGIN = 0.10           # margen alrededor del glifo
MAX_INK_FRAC = 0.45     # más tinta que esto es una mancha
SESSION_GAP = 300       # segundos sin envíos para considerar que empieza otra sesión
HASH_SIZE = 16

# distancia <= 2 son la misma imagen enviada dos veces.
DUP_MAX_DIST = 2
N_FOLDS = 20            # 3 folds test, 3 val, 14 train = 15/15/70


def list_samples(raw_dir):
    samples = []
    for class_dir in sorted(raw_dir.iterdir()):
        if not class_dir.is_dir() or class_dir.name.startswith(("~", ".")):
            continue
        subclase = class_dir.name
        clase = re.sub(r"_\d+$", "", subclase)
        for png in sorted(class_dir.glob("*.png")):
            samples.append({
                "id": f"{subclase}/{png.stem}",
                "path": png,
                "subclase": subclase,
                "clase": clase,
                "timestamp": int(png.stem.rsplit("-", 1)[1]),
            })
    return samples


def load_square(path):
    """Recorta el glifo y lo centra en un cuadrado, con la tinta en 255."""
    ink = np.array(Image.open(path).convert("RGBA"))[..., 3]
    rows = np.flatnonzero((ink > INK_THRESHOLD).any(axis=1))
    cols = np.flatnonzero((ink > INK_THRESHOLD).any(axis=0))
    if rows.size == 0:
        return None
    ink = ink[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    h, w = ink.shape
    side = int(max(h, w) * (1 + 2 * MARGIN))
    canvas = np.zeros((side, side), dtype=np.uint8)
    top, left = (side - h) // 2, (side - w) // 2
    canvas[top:top + h, left:left + w] = ink
    return canvas


def resize(square, size):
    return np.array(Image.fromarray(square).resize((size, size), Image.LANCZOS))


def dhash(square):
    small = np.array(Image.fromarray(square).resize((HASH_SIZE + 1, HASH_SIZE), Image.LANCZOS),
                     dtype=np.int16)
    return (small[:, 1:] > small[:, :-1]).flatten()


def find_near_duplicates(hashes):
    packed = np.packbits(hashes, axis=1)
    pairs = []
    for i in range(len(packed) - 1):
        dist = np.bitwise_count(packed[i + 1:] ^ packed[i]).sum(axis=1)
        for j in np.flatnonzero(dist <= DUP_MAX_DIST):
            pairs.append((i, i + 1 + j, int(dist[j])))
    return pairs


def assign_sessions(timestamps):
    """Agrupa los envíos seguidos en sesiones, para no repartir un mismo estilo entre train y test"""
    order = np.argsort(timestamps, kind="stable")
    sessions = np.empty(len(timestamps), dtype=int)
    current, prev = 0, None
    for idx in order:
        if prev is not None and timestamps[idx] - prev > SESSION_GAP:
            current += 1
        sessions[idx] = current
        prev = timestamps[idx]
    return sessions


def duplicates_to_drop(samples, pairs):
    """De cada par duplicado se queda una copia"""
    drop = {}
    for i, j, _ in pairs:
        if i in drop:
            continue
        if samples[i]["subclase"] == samples[j]["subclase"]:
            drop.setdefault(j, f"duplicado de {samples[i]['id']}")
        else:
            drop[i] = drop[j] = "duplicado con etiqueta distinta"
    return drop


def make_splits(labels, groups):
    sgkf = StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    split = np.empty(len(labels), dtype=object)
    for fold, (_, idx) in enumerate(sgkf.split(np.zeros(len(labels)), labels, groups)):
        split[idx] = "test" if fold < 3 else "val" if fold < 6 else "train"
    return split


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[32, 64])
    args = parser.parse_args()

    samples = list_samples(RAW_DIR)
    print(f"{len(samples)} imágenes en {len({s['subclase'] for s in samples})} subclases "
          f"({len({s['clase'] for s in samples})} palabras)")

    discarded = []
    squares, kept = [], []
    for s in samples:
        sq = load_square(s["path"])
        if sq is None:
            discarded.append((s["id"], "sin tinta"))
        elif (sq > 128).mean() > MAX_INK_FRAC:
            discarded.append((s["id"], "mancha rellena"))
        else:
            squares.append(sq)
            kept.append(s)
    samples = kept

    hashes = np.stack([dhash(sq) for sq in squares])
    pairs = find_near_duplicates(hashes)
    drop = duplicates_to_drop(samples, pairs)
    discarded += [(samples[i]["id"], reason) for i, reason in sorted(drop.items())]
    squares = [sq for i, sq in enumerate(squares) if i not in drop]
    samples = [s for i, s in enumerate(samples) if i not in drop]
    print(f"{len(pairs)} pares casi duplicados (distancia <= {DUP_MAX_DIST}); "
          f"{len(discarded)} imágenes descartadas en total, quedan {len(samples)}")

    timestamps = np.array([s["timestamp"] for s in samples])
    sessions = assign_sessions(timestamps)
    labels = np.array([s["subclase"] for s in samples])
    words = np.array([s["clase"] for s in samples])
    split = make_splits(labels, sessions)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ids = np.array([s["id"] for s in samples])
    for size in args.sizes:
        X = np.stack([resize(sq, size) for sq in squares])
        np.savez_compressed(OUT_DIR / f"glifos{size}.npz", X=X, ids=ids)
        # la normalización se calcula solo con train
        train = X[split == "train"] / 255.0
        stats = {"mean": float(train.mean()), "std": float(train.std())}
        with open(OUT_DIR / f"norm_stats{size}.json", "w") as f:
            json.dump(stats, f, indent=2)

    with open(OUT_DIR / "splits.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "subclase", "clase", "timestamp", "sesion", "split"])
        for s, ses, sp in zip(samples, sessions, split):
            writer.writerow([s["id"], s["subclase"], s["clase"], s["timestamp"], ses, sp])

    with open(OUT_DIR / "descartadas.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "motivo"])
        writer.writerows(discarded)

    print(f"{len(set(sessions))} sesiones (corte a {SESSION_GAP} s sin envíos)")
    for name in ("train", "val", "test"):
        mask = split == name
        print(f"  {name:5s} {mask.sum():6d} ({mask.mean():.1%}), "
              f"palabras: {len(set(words[mask]))}, subclases: {len(set(labels[mask]))}")
    missing = {c for c in set(words) for name in ("val", "test")
               if not ((words == c) & (split == name)).any()}
    if missing:
        print(f"  AVISO: palabras sin muestras en val o test: {sorted(missing)}")


if __name__ == "__main__":
    main()
