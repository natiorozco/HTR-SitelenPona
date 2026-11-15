"""Tabla de trade-off entre desempeño y costo: macro-F1 en test por semilla (de los CSV de predicciones)
y parámetros, segundos de entrenamiento, ms de inferencia por imagen, mejor época y dispositivo (del log).
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import LOGS_DIR, PREDS_DIR, RESULTS_DIR

ROLES = [("dummy", "trivial"), ("pixels_lr", "clásica (ablación)"), ("hog_lr", "clásica"),
         ("hcrnet", "literatura"), ("cnn", "propia"), ("resnet18", "propia")]
# contra este referente se escriben las relaciones de costo del cierre del módulo 2.3
BASE = "cnn_sinaug"


def rol(modelo):
    return next((r for prefijo, r in ROLES if modelo.startswith(prefijo)), "otra")


def orden(modelo):
    prefijos = [p for p, _ in ROLES]
    return (prefijos.index(next((p for p in prefijos if modelo.startswith(p)), "z")), modelo)


def f1_de(path, split):
    with open(path) as f:
        rows = [r for r in csv.DictReader(f) if r["split"] == split]
    return f1_score([r["y_true"] for r in rows], [r["y_pred"] for r in rows], average="macro")


def media_desv(valores):
    if not valores:
        return None, None
    return float(np.mean(valores)), float(np.std(valores))


def fmt(vals, dec=2, suf=""):
    if vals[0] is None:
        return "-"
    texto = f"{vals[0]:,.{dec}f}"
    if vals[1] == 0 or np.isnan(vals[1]):
        return texto + suf
    return f"{texto} ± {vals[1]:,.{dec}f}{suf}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["test", "val"], default="test")
    args = parser.parse_args()

    # macro-F1 por semilla, desde los CSV de predicciones
    f1s = defaultdict(list)
    for path in sorted(PREDS_DIR.glob("*_seed*.csv")):
        f1s[re.sub(r"_seed\d+$", "", path.stem)].append(f1_de(path, args.split))

    # costo por semilla, desde los logs (uno por corrida; en los baselines, uno solo)
    logs_por_modelo = defaultdict(list)
    for path in sorted(LOGS_DIR.glob("*.json")):
        with open(path) as f:
            log = json.load(f)
        logs_por_modelo[log.get("modelo") or re.sub(r"_seed\d+$", "", path.stem)].append(log)

    datos = {}
    for modelo in set(f1s) | set(logs_por_modelo):
        logs, f1_list = logs_por_modelo[modelo], f1s[modelo]
        valores = lambda campo: [log[campo] for log in logs if campo in log]
        datos[modelo] = {
            "rol": rol(modelo),
            "semillas": len(f1_list),
            "f1": media_desv(f1_list),
            "parametros": media_desv(valores("parametros")),
            "segundos": media_desv(valores("segundos_entrenamiento")),
            "ms": media_desv(valores("ms_inferencia_por_imagen")),
            "epoca": media_desv(valores("mejor_epoca")),
            "dispositivo": sorted({log["dispositivo"] for log in logs if "dispositivo" in log}) or ["-"],
        }

    out = RESULTS_DIR / "tradeoff.md"
    lineas = [f"# Trade-off entre desempeño y costo (macro-F1 en {args.split})",
              "",
              "| Modelo | Rol | Semillas | Macro-F1 | Parámetros | s entrenamiento | ms/imagen | Mejor época | Dispositivo |",
              "|---|---|---|---|---|---|---|---|---|"]
    for modelo in sorted(datos, key=orden):
        d = datos[modelo]
        lineas.append(f"| {modelo} | {d['rol']} | {d['semillas']} | {fmt(d['f1'], 4)} | "
                      f"{fmt(d['parametros'], 0)} | {fmt(d['segundos'], 1)} | {fmt(d['ms'], 3)} | "
                      f"{fmt(d['epoca'], 1)} | {', '.join(d['dispositivo'])} |")
    lineas += ["",
               "Los segundos y ms/imagen solo son comparables entre corridas del mismo dispositivo; "
               "las que tienen un valor distinto en Dispositivo corrieron en otro hardware."]
    dispositivos = {d for x in datos.values() for d in x["dispositivo"]} - {"-"}
    if len(dispositivos) > 1:
        lineas += ["", "## Comparabilidad",
                   "",
                   "Se entrenó en más de un dispositivo:"]
        for modelo in sorted(datos, key=orden):
            if datos[modelo]["dispositivo"] != ["-"]:
                lineas.append(f"- {modelo}: {', '.join(datos[modelo]['dispositivo'])}")

    lineas += ["",
               "Los baselines clásicos (dummy, píxeles + LR, HOG + LR) no son redes neuronales; no "
               "tienen parámetros que valga la pena contar, y su costo está en el ajuste del "
               "hiperparámetro, no en una corrida repetible. Por eso van con guion en esas columnas."]

    # relaciones de costo para responder si las arquitecturas grandes justifican su costo
    if BASE in datos and datos[BASE]["f1"][0] is not None:
        lineas += ["", "## Relaciones de costo frente a " + BASE, ""]
        base = datos[BASE]
        f1_hog = datos["hog_lr"]["f1"][0] if "hog_lr" in datos else None
        for modelo in ("cnn_aug", "resnet18_aug", "hcrnet_sinaug", "hcrnet_aug"):
            d = datos.get(modelo)
            if not d or d["f1"][0] is None:
                continue
            partes = [f"macro-F1 {fmt(d['f1'], 4)}"]
            if d["parametros"][0] is not None and base["parametros"][0]:
                partes.append(f"{d['parametros'][0] / base['parametros'][0]:.1f}x los parámetros")
            if d["segundos"][0] is not None and base["segundos"][0]:
                if set(base["dispositivo"]) == set(d["dispositivo"]):
                    partes.append(f"{d['segundos'][0] / base['segundos'][0]:.1f}x el tiempo de "
                                  f"entrenamiento ({base['dispositivo'][0]} vs {d['dispositivo'][0]})")
                else:
                    partes.append(f"tiempo de entrenamiento no comparable ({base['dispositivo'][0]} "
                                  f"vs {d['dispositivo'][0]})")
            if d["ms"][0] is not None and base["ms"][0]:
                partes.append(f"{d['ms'][0] / base['ms'][0]:.1f}x el ms/imagen")
            if f1_hog is not None:
                partes.append(f"{(d['f1'][0] - f1_hog) * 100:+.2f} pp de macro-F1 frente a hog_lr")
            lineas.append(f"- {modelo}: " + ", ".join(partes) + ".")

    out.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"-> {out}")
    for linea in lineas:
        if linea.startswith("|"):
            print(linea)


if __name__ == "__main__":
    main()
