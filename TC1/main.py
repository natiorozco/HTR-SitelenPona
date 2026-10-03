"""Punto de entrada único.

Uso:
    python main.py <instancia> --agente busqueda --semilla 1 --tiempo 10 [--salida sol.txt]
"""

import argparse
import os
import sys
import time

from tileup import IllegalMoveError, InstanceError, load_instance, play, write_solution
from agents import AGENTS


def safety_margin(limit: float) -> float:
    """Tiempo que se reserva para reconstruir, validar y escribir la solución."""
    return max(0.05, min(1.0, 0.1 * limit))


def main(argv=None) -> int:
    t0 = time.perf_counter()
    ap = argparse.ArgumentParser(description="Agentes para TileUp")
    ap.add_argument("instancia", help="ruta del archivo de instancia")
    ap.add_argument("--agente", required=True, choices=sorted(AGENTS))
    ap.add_argument("--semilla", type=int, default=0)
    ap.add_argument("--tiempo", type=float, default=10.0, help="límite en segundos")
    ap.add_argument("--salida", default=None,
                    help="archivo de solución (por defecto soluciones/<instancia>_<agente>_s<semilla>.txt)")
    args = ap.parse_args(argv)

    if args.tiempo <= 0:
        print("error: --tiempo debe ser positivo", file=sys.stderr)
        return 2

    try:
        inst = load_instance(args.instancia)
    except InstanceError as e:
        print(f"error en la instancia: {e}", file=sys.stderr)
        return 1

    salida = args.salida
    if salida is None:
        base = os.path.splitext(os.path.basename(args.instancia))[0]
        salida = os.path.join("soluciones", f"{base}_{args.agente}_s{args.semilla}.txt")

    deadline = t0 + args.tiempo - safety_margin(args.tiempo)
    result = AGENTS[args.agente](inst, args.semilla, deadline)

    # El resultado del agente se reproduce con el motor: nunca se confía en él.
    try:
        final = play(inst, result.placements, stop_on_terminal=False)
    except IllegalMoveError as e:
        print(f"error interno: el agente propuso una jugada ilegal: {e}", file=sys.stderr)
        return 3
    moves = [final.coords(i) for i in result.placements]

    try:
        out_dir = os.path.dirname(salida)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        write_solution(salida, moves, final)
    except OSError as e:
        print(f"error: no se pudo escribir '{salida}': {e.strerror}", file=sys.stderr)
        return 1

    elapsed = time.perf_counter() - t0
    print(f"agente={args.agente} semilla={args.semilla} instancia={args.instancia}")
    print(f"estado={final.status().value}")
    print(f"colocadas={final.placed}")
    print(f"ocupadas={final.occupied}")
    print(f"mayor={final.max_value}")
    print(f"tiempo={elapsed:.3f}")
    print(f"{result.effort_name}={result.effort}")
    for k, v in result.extra.items():
        print(f"{k}={v}")
    print(f"solucion={salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
