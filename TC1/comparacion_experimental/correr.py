"""Corre los dos agentes sobre todas las instancias de la comparación como si fuera
un usuario desde main. Coloca los resultados en la carpeta de soluciones y las métricas en el 
csv de resultados.
"""

import argparse
import csv
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from generar import CONFIGS, SEEDS, instance_name

HERE = os.path.dirname(os.path.abspath(__file__))
TC1 = os.path.dirname(HERE)
INST_DIR = os.path.join(HERE, "instancias")
SOL_DIR = os.path.join(HERE, "soluciones")
CSV_PATH = os.path.join(HERE, "resultados.csv")

AGENTS = ["busqueda", "evolutivo"]
COLUMNS = ["n", "k", "m", "semilla", "agente", "limite", "codigo_salida", "estado", "colocadas",
           "ocupadas", "mayor", "tiempo", "esfuerzo", "esfuerzo_nombre", "error"]


def run_one(job, limit):
    """Corre main.py para una instancia y un agente, y devuelve sus métricas."""
    (n, k, m), seed, agent = job
    name = instance_name(n, k, m, seed)
    solution = os.path.join(SOL_DIR, name.replace(".txt", f"_{agent}.txt"))
    cmd = [sys.executable, "main.py", os.path.join(INST_DIR, name),
           "--agente", agent, "--semilla", str(seed), "--tiempo", str(limit),
           "--salida", solution]
    row = {"n": n, "k": k, "m": m, "semilla": seed, "agente": agent, "limite": limit}
    try:
        proc = subprocess.run(cmd, cwd=TC1, capture_output=True, text=True,
                              timeout=limit + 30)
    except subprocess.TimeoutExpired:
        # si se pasó mucho del límite es un fallo
        return {**row, "codigo_salida": "timeout", "error": "no terminó a tiempo"}

   
    out = dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)
    effort_name = next((key for key in ("nodos_expandidos", "evaluaciones_aptitud") if key in out), "")
    error = ""
    if proc.returncode != 0:
        # última línea del error
        lines = proc.stderr.strip().splitlines()
        error = lines[-1] if lines else "terminó con error"
    return {
        **row,
        "codigo_salida": proc.returncode,
        "estado": out.get("estado", ""),
        "colocadas": out.get("colocadas", ""),
        "ocupadas": out.get("ocupadas", ""),
        "mayor": out.get("mayor", ""),
        "tiempo": out.get("tiempo", ""),
        "esfuerzo": out.get(effort_name, ""),
        "esfuerzo_nombre": effort_name,
        "error": error,
    }


def main():
    parser = argparse.ArgumentParser(description="Corre la comparación experimental")
    parser.add_argument("--tiempo", type=float, default=10.0, help="límite por corrida en segundos")
    parser.add_argument("--paralelo", type=int, default=4, help="corridas simultáneas")
    args = parser.parse_args()

    os.makedirs(SOL_DIR, exist_ok=True)
    jobs = [(config, seed, agent) for config in CONFIGS for seed in SEEDS for agent in AGENTS]
    print(f"{len(jobs)} corridas de {args.tiempo:g} s, {args.paralelo} al mismo tiempo")

    start = time.perf_counter()
    with ThreadPoolExecutor(args.paralelo) as pool:
        rows = list(pool.map(lambda job: run_one(job, args.tiempo), jobs))

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    failed = sum(1 for row in rows if row["codigo_salida"] != 0)
    print(f"listo en {time.perf_counter() - start:.0f} s; {failed} corridas con error")
    print(f"resultados en {CSV_PATH}")


if __name__ == "__main__":
    main()
