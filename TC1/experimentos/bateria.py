"""Batería experimental: escalabilidad de ambos agentes en N y K.

Uso (desde la carpeta TC1):
    python experimentos/bateria.py
    python experimentos/bateria.py --N 4 5 6 --K 4 12 24 --M 200 --semillas 1 2 3 --tiempo 5
    python experimentos/bateria.py --solo-resumen     # rehace tablas y gráficas desde el CSV

Para cada combinación de N, K y semilla:
  1. genera la instancia con generador.py (la semilla fija la secuencia),
  2. corre cada agente con main.py como un proceso aparte, con la misma
     semilla y el mismo límite de tiempo, igual que lo haría el evaluador,
  3. guarda la solución y las métricas que main.py imprime.

Las corridas son secuenciales a propósito: correrlas en paralelo haría que
compitan por el procesador y los tiempos dejarían de ser comparables.

Salidas (en experimentos/):
  instancias/   las instancias generadas
  soluciones/   una solución por agente, instancia y semilla
  resultados/resultados.csv   una fila por corrida
  resultados/resumen.md       media ± desviación por configuración y gráficas
  resultados/*.svg            gráficas
"""

import argparse
import csv
import os
import statistics
import subprocess
import sys
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                 # carpeta TC1
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from agents import AGENTS                    # noqa: E402  (solo para saber los nombres)
from generador import generate               # noqa: E402
from graficas import line_panels             # noqa: E402
from main import safety_margin               # noqa: E402

# Nombre que aparece en tablas y gráficas. Un agente nuevo que no esté aquí
# se muestra con su nombre tal cual.
AGENT_LABEL = {"busqueda": "Búsqueda (DFS con poda)",
               "evolutivo": "Evolutivo (genético sobre pesos)"}
FIELDS = ["agente", "N", "K", "M", "semilla", "estado", "colocadas", "ocupadas", "mayor",
          "tiempo", "esfuerzo", "medida_esfuerzo", "corte_por_tiempo", "fraccion_colocada",
          "extra", "instancia", "solucion", "error"]

# Líneas de main.py que son métricas comunes a todos los agentes.
COMMON_KEYS = {"agente", "estado", "colocadas", "ocupadas", "mayor", "tiempo", "solucion"}


def label(agent):
    return AGENT_LABEL.get(agent, agent)


def stopped_by_clock(elapsed, limit):
    """¿El agente se detuvo porque se le acabó el tiempo?

    main.py le da al agente el límite menos un margen (`safety_margin`). Si el
    tiempo total llegó a ese plazo, lo detuvo el reloj; si terminó bastante
    antes, se detuvo por un criterio propio (encontró el óptimo, agotó la
    búsqueda, etc.). Se usa la misma regla para ambos agentes, sin depender de
    lo que cada uno informe.
    """
    return elapsed >= 0.95 * (limit - safety_margin(limit))


# ----------------------------------------------------------------- corridas
def parse_output(stdout):
    """Convierte las líneas `clave=valor` de main.py en un diccionario.

    main.py imprime siempre, en este orden: agente, estado, colocadas,
    ocupadas, mayor, tiempo, <medida de esfuerzo>=<valor>, los datos extra
    del agente y solucion. La medida de esfuerzo se reconoce por ir justo
    después de `tiempo`, así funciona con cualquier agente.
    """
    values, order = {}, []
    for line in stdout.splitlines():
        line = line.strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if " " in key:
            continue
        values[key] = value
        order.append(key)
    effort_key = order[order.index("tiempo") + 1] if "tiempo" in order[:-1] else ""
    return values, effort_key


def run_one(instance_path, agent, seed, limit, solution_path):
    """Corre main.py y devuelve sus métricas como diccionario."""
    cmd = [sys.executable, os.path.join(ROOT, "main.py"), instance_path,
           "--agente", agent, "--semilla", str(seed), "--tiempo", str(limit),
           "--salida", solution_path]
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=limit + 30)
    except subprocess.TimeoutExpired:
        return {"error": "el proceso no terminó"}
    if proc.returncode != 0:
        return {"error": (proc.stderr.strip() or f"código {proc.returncode}").splitlines()[-1]}

    out, effort_key = parse_output(proc.stdout)
    elapsed = float(out.get("tiempo", 0))
    # Lo que cada agente informa además de lo común (generaciones, pesos,
    # completo, ...) se guarda tal cual en una sola columna.
    extra = "; ".join(f"{k}={v}" for k, v in out.items()
                      if k not in COMMON_KEYS and k != effort_key)
    return {
        "estado": out.get("estado", ""),
        "colocadas": int(out.get("colocadas", 0)),
        "ocupadas": int(out.get("ocupadas", 0)),
        "mayor": int(out.get("mayor", 0)),
        "tiempo": elapsed,
        "esfuerzo": int(out.get(effort_key, 0) or 0),
        "medida_esfuerzo": effort_key,
        "corte_por_tiempo": "si" if stopped_by_clock(elapsed, limit) else "no",
        "extra": extra,
        "error": "",
    }


def run_battery(args):
    inst_dir = os.path.join(HERE, "instancias")
    sol_dir = os.path.join(HERE, "soluciones")
    res_dir = os.path.join(HERE, "resultados")
    for d in (inst_dir, sol_dir, res_dir):
        os.makedirs(d, exist_ok=True)

    combos = [(n, k, s) for n in args.N for k in args.K for s in args.semillas]
    total = len(combos) * len(args.agentes)
    print(f"{total} corridas, hasta {args.tiempo:g} s cada una "
          f"(~{total * args.tiempo / 60:.1f} min como máximo)")

    rows = []
    done = 0
    t_start = time.perf_counter()
    for n, k, s in combos:
        name = f"gen_N{n}_K{k}_M{args.M}_s{s}"
        inst_path = os.path.join(inst_dir, name + ".txt")
        with open(inst_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(generate(n, k, args.M, s))
        for agent in args.agentes:
            sol_path = os.path.join(sol_dir, f"{name}_{agent}.txt")
            r = run_one(inst_path, agent, s, args.tiempo, sol_path)
            r.update({"agente": agent, "N": n, "K": k, "M": args.M, "semilla": s,
                      "instancia": os.path.relpath(inst_path, ROOT).replace("\\", "/"),
                      "solucion": os.path.relpath(sol_path, ROOT).replace("\\", "/")})
            r["fraccion_colocada"] = round(r.get("colocadas", 0) / args.M, 4) if args.M else 1.0
            rows.append(r)
            done += 1
            status = r["error"] or (f"colocadas={r['colocadas']}/{args.M} ocupadas={r['ocupadas']} "
                                    f"tiempo={r['tiempo']:.2f}s corte={r['corte_por_tiempo']}")
            print(f"[{done}/{total}] N={n} K={k} s={s} {agent:9s} {status}", flush=True)

    csv_path = os.path.join(res_dir, "resultados.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    print(f"\n{csv_path}  ({time.perf_counter() - t_start:.0f} s en total)")
    return csv_path


# ------------------------------------------------------------------ resumen
def load_rows(csv_path):
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["error"]:
                continue
            for k in ("N", "K", "M", "semilla", "colocadas", "ocupadas", "mayor", "esfuerzo"):
                r[k] = int(r[k])
            for k in ("tiempo", "fraccion_colocada"):
                r[k] = float(r[k])
            rows.append(r)
    return rows


def mean_sd(values):
    m = statistics.mean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return m, sd


def fmt(values, digits=2):
    m, sd = mean_sd(values)
    return f"{m:.{digits}f} ± {sd:.{digits}f}"


def summarize(csv_path, limit):
    res_dir = os.path.dirname(csv_path)
    rows = load_rows(csv_path)
    if not rows:
        print("no hay corridas válidas en el CSV")
        return

    groups = defaultdict(list)
    for r in rows:
        groups[(r["agente"], r["N"], r["K"], r["M"])].append(r)
    present = {k[0] for k in groups}
    agents = [a for a in AGENTS if a in present] + sorted(present - set(AGENTS))
    Ns = sorted({k[1] for k in groups})
    Ks = sorted({k[2] for k in groups})
    Ms = sorted({k[3] for k in groups})

    # ---- gráficas
    def panels(metric, series_key, x_key):
        out = {}
        for a in agents:
            per = defaultdict(dict)
            for (ga, n, k, m), rs in groups.items():
                if ga != a:
                    continue
                series = f"N={n}" if series_key == "N" else f"K={k}"
                x = k if x_key == "K" else n
                vals = [r[metric] for r in rs]
                mm, sd = mean_sd(vals)
                per[series][x] = (mm, sd, len(vals))
            out[label(a)] = dict(sorted(per.items(), key=lambda kv: int(kv[0].split("=")[1])))
        return out

    sub = f"M = {', '.join(map(str, Ms))} fichas · media de {len(set(r['semilla'] for r in rows))} semillas · barras: ±1 desviación estándar"
    charts = [
        ("fraccion_vs_K.svg", "Fracción de fichas colocadas al crecer K", "Cantidad de colores (K)",
         "Fracción colocada", Ks, panels("fraccion_colocada", "N", "K"), 1.0, None, "{:.1f}"),
        ("fraccion_vs_N.svg", "Fracción de fichas colocadas al crecer N", "Lado del tablero (N)",
         "Fracción colocada", Ns, panels("fraccion_colocada", "K", "N"), 1.0, None, "{:.1f}"),
        ("tiempo_vs_K.svg", "Tiempo de cómputo al crecer K", "Cantidad de colores (K)",
         "Tiempo (s)", Ks, panels("tiempo", "N", "K"), None,
         (limit, f"límite = {limit:g} s") if limit else None, "{:.1f}"),
    ]
    for fname, title, xl, yl, xs, pn, ymax, ref, yf in charts:
        line_panels(os.path.join(res_dir, fname), title, sub, xl, yl, xs, pn,
                    y_max=ymax, ref_line=ref, y_fmt=yf)

    # ---- tablas
    lines = ["# Resultados de la batería experimental", "",
             f"Generado por `experimentos/bateria.py` a partir de `resultados.csv` "
             f"({len(rows)} corridas válidas). Cada celda es media ± desviación estándar "
             f"entre semillas. \"Corte por tiempo\" cuenta las corridas que llegaron al plazo "
             f"del agente (límite menos el margen de main.py) en lugar de detenerse por un "
             f"criterio propio.", ""]
    for a in agents:
        lines += [f"## {label(a)}", "",
                  "| N | K | M | colocadas | fracción colocada | ocupadas | tiempo (s) | esfuerzo | victorias | corte por tiempo |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for (ga, n, k, m), rs in sorted(groups.items()):
            if ga != a:
                continue
            wins = sum(r["estado"] == "victoria" for r in rs)
            cuts = sum(r["corte_por_tiempo"] == "si" for r in rs)
            lines.append(f"| {n} | {k} | {m} | {fmt([r['colocadas'] for r in rs], 1)} | "
                         f"{fmt([r['fraccion_colocada'] for r in rs])} | "
                         f"{fmt([r['ocupadas'] for r in rs], 1)} | {fmt([r['tiempo'] for r in rs])} | "
                         f"{fmt([r['esfuerzo'] for r in rs], 0)} | {wins}/{len(rs)} | {cuts}/{len(rs)} |")
        effort = rows[[r["agente"] for r in rows].index(a)]["medida_esfuerzo"]
        lines += ["", f"Esfuerzo = `{effort}`.", ""]

    lines += ["## Gráficas", "",
              "![Fracción colocada vs K](fraccion_vs_K.svg)", "",
              "![Fracción colocada vs N](fraccion_vs_N.svg)", "",
              "![Tiempo vs K](tiempo_vs_K.svg)", ""]
    md_path = os.path.join(res_dir, "resumen.md")
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(md_path)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Batería experimental de TileUp")
    ap.add_argument("--N", type=int, nargs="+", default=[4, 5, 6])
    ap.add_argument("--K", type=int, nargs="+", default=[4, 12, 24])
    ap.add_argument("--M", type=int, default=200)
    ap.add_argument("--semillas", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--tiempo", type=float, default=5.0, help="límite por corrida (s)")
    ap.add_argument("--agentes", nargs="+", default=list(AGENTS), choices=list(AGENTS),
                    help="por defecto, todos los agentes registrados en agents/__init__.py")
    ap.add_argument("--solo-resumen", action="store_true",
                    help="no corre nada; rehace tablas y gráficas desde resultados.csv")
    args = ap.parse_args(argv)

    csv_path = os.path.join(HERE, "resultados", "resultados.csv")
    if not args.solo_resumen:
        csv_path = run_battery(args)
    elif not os.path.exists(csv_path):
        print(f"error: no existe {csv_path}; corra primero la batería", file=sys.stderr)
        return 1
    summarize(csv_path, args.tiempo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
