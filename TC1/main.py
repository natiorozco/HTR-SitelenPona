"""Punto de entrada único.

    python3 main.py <instancia> --agent busqueda --time 10 \
        [--output soluciones/mia.txt]
"""

import argparse
import os
import sys
import time

from agents import AGENTS
from tileup import IllegalMoveError, InstanceError, load_instance, play, write_solution


def safety_margin(limit: float) -> float:
    """Tiempo que se reserva para reproducir y escribir la solución."""
    return max(0.05, min(1.0, 0.1 * limit))


def main(argv=None) -> int:
    t0 = time.perf_counter()
    ap = argparse.ArgumentParser(description="Agentes de búsqueda y evolutivos para TileUp")
    ap.add_argument("instancia", help="ruta del archivo de instancia")
    ap.add_argument("--agente", "--agent", dest="agent", required=True, choices=sorted(AGENTS))
    ap.add_argument("--semilla", "--seed", dest="seed", type=int, default=0,
                    help="semilla de la que sale todo el azar (por defecto 0)")
    ap.add_argument("--tiempo", "--time", dest="time", type=float, default=10.0,
                    help="límite total en segundos (por defecto 10)")
    ap.add_argument("--salida", "--output", dest="output", default=None,
                    help="archivo de solución (por defecto soluciones/<instancia>_<agente>_s<semilla>.txt)")
    args = ap.parse_args(argv)

    if args.time <= 0:
        print("error: --tiempo debe ser positivo", file=sys.stderr)
        return 2
    try:
        inst = load_instance(args.instancia)
    except InstanceError as e:
        print(f"error en la instancia: {e}", file=sys.stderr)
        return 1

    out_path = args.output
    if out_path is None:
        base = os.path.splitext(os.path.basename(args.instancia))[0]
        out_path = os.path.join("soluciones", f"{base}_{args.agent}_s{args.seed}.txt")

    # Se reserva un margen para reproducir y escribir la solución, de modo que el
    # programa no termine después del límite pedido.
    res = AGENTS[args.agent](inst, args.seed, t0 + args.time - safety_margin(args.time))

    # La solución del agente se reproduce con el motor: nunca se confía en ella.
    try:
        final = play(inst, res.placements, stop_on_terminal=False)
    except IllegalMoveError as e:
        print(f"error interno: el agente propuso una jugada ilegal: {e}", file=sys.stderr)
        return 3
    if final.placed != len(res.placements):
        print("error interno: el motor reprodujo menos jugadas de las que "
              f"propuso el agente ({final.placed} de {len(res.placements)})", file=sys.stderr)
        return 3

    try:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        write_solution(out_path, [final.coords(i) for i in res.placements], final)
    except OSError as e:
        print(f"error: no se pudo escribir '{out_path}': {e.strerror}", file=sys.stderr)
        return 1

    elapsed = time.perf_counter() - t0
    print(f"agente={args.agent} semilla={args.seed} instancia={args.instancia}")
    print(f"estado={final.status().value}")
    print(f"colocadas={final.placed}")
    print(f"ocupadas={final.occupied}")
    print(f"mayor={final.max_value}")
    print(f"tiempo={elapsed:.3f}")
    print(f"{res.effort_name}={res.effort}")
    for k, v in res.extra.items():
        print(f"{k}={v}")
    print(f"solucion={out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())