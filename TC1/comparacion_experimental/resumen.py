"""Resume resultados.csv en tablas para resultados.md
"""

import csv
import os
import statistics
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))   # para importar tileup 

from tileup import load_instance 

from generar import CONFIGS, SEEDS, instance_name  

CSV_PATH = os.path.join(HERE, "resultados.csv")
MD_PATH = os.path.join(HERE, "resultados.md")
AGENTS = ["busqueda", "evolutivo"]


def bounds(n, k, m, seed):
    """máximo de fichas colocables, mínimo de celdas ocupadas al ganar"""
    instance = load_instance(os.path.join(HERE, "instancias", instance_name(n, k, m, seed)))
    seen = set()
    max_placed = instance.m
    for index, tile in enumerate(instance.tiles):
        seen.add(tile.color)
        if len(seen) >= n * n and index < instance.m - 1:
            max_placed = index + 1
            break
    return max_placed, len({tile.color for tile in instance.tiles})


def mean_sd(values, decimals=1):
    """promedio ± desviación. La desviación es la muestral (n - 1)."""
    if not values:
        return "—"
    mean = statistics.mean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return f"{mean:.{decimals}f} ± {sd:.{decimals}f}"


def main():
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ok = [row for row in rows if row["codigo_salida"] == "0"]
    failed = [row for row in rows if row["codigo_salida"] != "0"]

    
    groups = defaultdict(list)
    for row in ok:
        config = (int(row["n"]), int(row["k"]), int(row["m"]))
        groups[config, row["agente"]].append(row)

    limit = rows[0]["limite"] if rows else "?"
    seeds = ", ".join(str(seed) for seed in SEEDS[:-1]) + f" y {SEEDS[-1]}"
    out = [
        "# Resultados de la comparación experimental",
        "",
        f"Límite de tiempo: {limit} s por corrida.",
        f"Cada configuración tiene {len(SEEDS)} instancias (semillas {seeds}).",
        f"Los valores son promedio ± desviación estándar entre las {len(SEEDS)} semillas.",
        "",
        "## Configuraciones",
        "",
        "| N | K | M | Celdas (N²) |",
        "|---|---|---|---|",
    ]
    for n, k, m in CONFIGS:
        out.append(f"| {n} | {k} | {m} | {n * n} |")

    out += [
        "",
        "## Resumen por configuración",
        "",
        "| Configuración (N, K, M) | Agente | Victorias | Colocadas | Cota colocadas | Ocupadas | Cota ocupadas | Tiempo (s) | Esfuerzo |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for n, k, m in CONFIGS:
        instance_bounds = [bounds(n, k, m, seed) for seed in SEEDS]
        max_placed = [b[0] for b in instance_bounds]
        min_occupied = [b[1] for b in instance_bounds]
        for agent in AGENTS:
            runs = groups.get(((n, k, m), agent), [])
            wins = sum(1 for row in runs if row["estado"] == "victoria")
            effort_name = runs[0]["esfuerzo_nombre"].replace("_", " ") if runs else ""
            out.append(
                f"| {n}×{n}, K={k}, M={m} | {agent} | {wins}/{len(SEEDS)} "
                f"| {mean_sd([int(r['colocadas']) for r in runs])} | {mean_sd(max_placed)} "
                f"| {mean_sd([int(r['ocupadas']) for r in runs])} | {mean_sd(min_occupied)} "
                f"| {mean_sd([float(r['tiempo']) for r in runs], 2)} "
                f"| {mean_sd([int(r['esfuerzo']) for r in runs], 0)} {effort_name} |"
            )

    out += [
        "",
        "## Detalle por instancia",
        "",
        "| Instancia | Agente | Estado | Colocadas | Ocupadas | Mayor | Tiempo (s) | Esfuerzo |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        name = instance_name(row["n"], row["k"], row["m"], row["semilla"]).replace(".txt", "")
        if row["codigo_salida"] != "0":
            out.append(f"| {name} | {row['agente']} | **falló** | — | — | — | — | {row['error']} |")
            continue
        out.append(
            f"| {name} | {row['agente']} | {row['estado']} | {row['colocadas']} | {row['ocupadas']} "
            f"| {row['mayor']} | {row['tiempo']} | {row['esfuerzo']} {row['esfuerzo_nombre'].replace('_', ' ')} |"
        )

    if failed:
        out += ["", f"**Corridas con error: {len(failed)}.** Ver la columna Esfuerzo del detalle para el mensaje."]

    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"tablas en {MD_PATH}")


if __name__ == "__main__":
    main()
