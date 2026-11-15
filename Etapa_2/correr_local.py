"""Corre toda la Etapa 2 en la compu, igual que correr_etapa2.ipynb.

Si se corta, volver a correrlo: se salta las corridas que ya tienen log.
    .venv-tf/bin/python Etapa_2/correr_local.py              # sigue donde quedó
    .venv-tf/bin/python Etapa_2/correr_local.py --desde-cero # borra results/ y empieza de nuevo
"""

import argparse
import itertools
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ETAPA2 = Path(__file__).resolve().parent
RESULTS = ETAPA2 / "results"
LOGS = RESULTS / "logs"
SEMILLAS = [0, 1, 2, 3, 4]

BUSQUEDA = {
    "cnn_sinaug":   ("--model cnn --aug none",
                     {"lr": [3e-4, 1e-3, 3e-3], "batch": [64, 128], "freeze": [0]}),
    "cnn_aug":      ("--model cnn --aug trad",
                     {"lr": [3e-4, 1e-3, 3e-3], "batch": [64, 128], "freeze": [0]}),
    "resnet18_aug": ("--model resnet18 --aug trad",
                     {"lr": [1e-4, 3e-4, 1e-3], "batch": [64], "freeze": [0, 3]}),
}
HCRNET = {"hcrnet_sinaug": "--aug none", "hcrnet_aug": "--aug trad",
          "hcrnet_aug_elastica": "--aug trad --elastica"}
INICIO = time.time()


def correr(script, args="", obligatorio=True):
    reloj = time.strftime("%H:%M")
    print(f"\n[{reloj}, {(time.time() - INICIO) / 3600:.1f} h] {script} {args}", flush=True)
    r = subprocess.run([sys.executable, str(ETAPA2 / script), *args.split()])
    if r.returncode != 0:
        if obligatorio:
            sys.exit(f"falló {script} {args}")
        print(f"(falló {script} {args}, sigo con lo demás)")


def ya_corrio(log):
    hecho = (LOGS / f"{log}.json").exists()
    if hecho:
        print(f"ya estaba: {log}")
    return hecho


def mejor_config(nombre):
    logs = [json.loads(p.read_text()) for p in (LOGS / "busqueda").glob(f"{nombre}_seed0_*.json")]
    print(nombre)
    for l in sorted(logs, key=lambda l: -l["mejor_val_macro_f1"]):
        c = l["config"]
        print(f"  lr={c['lr']:<7} batch={c['batch']:<4} freeze={c['freeze_epochs']}  "
              f"val macro-F1={l['mejor_val_macro_f1']:.4f}  ({l['segundos_entrenamiento']:.0f} s)")
    c = max(logs, key=lambda l: l["mejor_val_macro_f1"])["config"]
    return f"--lr {c['lr']} --batch {c['batch']} --freeze-epochs {c['freeze_epochs']}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--desde-cero", action="store_true", help="borra results/ antes de empezar")
    if parser.parse_args().desde_cero and RESULTS.exists():
        shutil.rmtree(RESULTS)

    # baselines
    if not list((RESULTS / "preds").glob("dummy_*.csv")):
        correr("baselines/dummy.py")
    for f in ("pixels", "hog"):
        if not ya_corrio(f"{f}_lr"):
            correr("baselines/hog_lr.py", f"--features {f}")

    # búsqueda de hiperparámetros de PyTorch (una semilla, solo validación)
    for nombre, (base, grilla) in BUSQUEDA.items():
        for lr, batch, fr in itertools.product(*grilla.values()):
            if not ya_corrio(f"busqueda/{nombre}_seed0_lr{lr}_b{batch}_wd0.0001_f{fr}"):
                correr("torch_models/train.py",
                       f"{base} --lr {lr} --batch {batch} --freeze-epochs {fr} --seed 0 --search")

    elegida = {nombre: mejor_config(nombre) for nombre in BUSQUEDA}
    (RESULTS / "configuracion_elegida.json").write_text(json.dumps(elegida, indent=1))
    print("elegida:", json.dumps(elegida, indent=1))

    # corridas finales: 5 semillas
    for nombre, (base, _) in BUSQUEDA.items():
        for s in SEMILLAS:
            if not ya_corrio(f"{nombre}_seed{s}"):
                correr("torch_models/train.py", f"{base} {elegida[nombre]} --seed {s}")
    for nombre, config in HCRNET.items():
        for s in SEMILLAS:
            if not ya_corrio(f"{nombre}_seed{s}"):
                correr("hcrnet/train_hcrnet.py", f"{config} --seed {s}")

    # evaluación, trade-off y Grad-CAM
    correr("evaluate.py", "--split val", obligatorio=False)
    correr("evaluate.py", "--split test", obligatorio=False)
    correr("tradeoff.py", obligatorio=False)
    for config in ("--model cnn --aug none", "--model cnn --aug trad", "--model resnet18 --aug trad"):
        correr("xai/gradcam_torch.py", f"{config} --seed 0", obligatorio=False)
    correr("xai/gradcam_tf.py", "--run hcrnet_aug --seed 0", obligatorio=False)

    print(f"\nlisto en {(time.time() - INICIO) / 3600:.1f} h")


if __name__ == "__main__":
    main()
